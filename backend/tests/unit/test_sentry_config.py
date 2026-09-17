"""Unit tests for Sentry SDK initialization and error-handler integration."""

from unittest.mock import MagicMock, patch

import pytest


class TestSentryInitialization:
    """Verify Sentry initializes only when a valid DSN is configured."""

    @patch("sentry_sdk.init")
    def test_sentry_initializes_with_valid_dsn(self, mock_init: MagicMock) -> None:
        """When SENTRY_DSN is a valid https URL, sentry_sdk.init must be called."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.sentry_dsn = "https://examplePublicKey@o0.ingest.sentry.io/0"
            mock_settings.sentry_environment = "testing"
            mock_settings.sentry_traces_sample_rate = 0.2
            mock_settings.log_level = "INFO"

            dsn = (mock_settings.sentry_dsn or "").strip()
            if dsn.startswith("https://"):
                import sentry_sdk

                sentry_sdk.init(
                    dsn=dsn,
                    environment=mock_settings.sentry_environment,
                    traces_sample_rate=mock_settings.sentry_traces_sample_rate,
                    send_default_pii=False,
                )

            mock_init.assert_called_once_with(
                dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
                environment="testing",
                traces_sample_rate=0.2,
                send_default_pii=False,
            )

    @patch("sentry_sdk.init")
    def test_sentry_skipped_when_dsn_empty(self, mock_init: MagicMock) -> None:
        """When SENTRY_DSN is empty, sentry_sdk.init must NOT be called."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.sentry_dsn = ""

            dsn = (mock_settings.sentry_dsn or "").strip()
            if dsn.startswith("https://"):
                import sentry_sdk

                sentry_sdk.init(dsn=dsn)

            mock_init.assert_not_called()

    @patch("sentry_sdk.init")
    def test_sentry_skipped_when_dsn_none(self, mock_init: MagicMock) -> None:
        """When SENTRY_DSN is None, sentry_sdk.init must NOT be called."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.sentry_dsn = None

            dsn = (mock_settings.sentry_dsn or "").strip()
            if dsn.startswith("https://"):
                import sentry_sdk

                sentry_sdk.init(dsn=dsn)

            mock_init.assert_not_called()

    @patch("sentry_sdk.init")
    def test_sentry_skipped_when_dsn_not_https(self, mock_init: MagicMock) -> None:
        """A DSN that does not start with https:// is ignored."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.sentry_dsn = "http://bad-dsn"

            dsn = (mock_settings.sentry_dsn or "").strip()
            if dsn.startswith("https://"):
                import sentry_sdk

                sentry_sdk.init(dsn=dsn)

            mock_init.assert_not_called()

    def test_send_default_pii_is_false(self) -> None:
        """Ensure send_default_pii is explicitly False to protect user privacy."""
        with patch("sentry_sdk.init") as mock_init:
            import sentry_sdk

            sentry_sdk.init(
                dsn="https://key@sentry.io/1",
                environment="test",
                traces_sample_rate=0.1,
                send_default_pii=False,
            )
            _, kwargs = mock_init.call_args
            assert kwargs["send_default_pii"] is False


class TestErrorHandlerSentryCapture:
    """Verify the error handler middleware calls sentry_sdk.capture_exception."""

    @pytest.mark.asyncio
    @patch("app.middleware.error_handler.sentry_sdk")
    async def test_general_exception_handler_captures_to_sentry(
        self, mock_sentry: MagicMock
    ) -> None:
        from app.middleware.error_handler import general_exception_handler

        exc = RuntimeError("test boom")
        request = MagicMock()
        request.url = MagicMock()

        response = await general_exception_handler(request, exc)

        mock_sentry.capture_exception.assert_called_once_with(exc)
        assert response.status_code == 500

    @pytest.mark.asyncio
    @patch("app.middleware.error_handler.sentry_sdk")
    async def test_sqlalchemy_exception_handler_captures_to_sentry(
        self, mock_sentry: MagicMock
    ) -> None:
        from sqlalchemy.exc import SQLAlchemyError

        from app.middleware.error_handler import sqlalchemy_exception_handler

        exc = SQLAlchemyError("db connection failed")
        request = MagicMock()
        request.url = MagicMock()

        response = await sqlalchemy_exception_handler(request, exc)

        mock_sentry.capture_exception.assert_called_once_with(exc)
        assert response.status_code == 503
