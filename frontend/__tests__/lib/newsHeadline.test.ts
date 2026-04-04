import { shortNewsLinkLabel } from "@/lib/format/newsHeadline"

describe("shortNewsLinkLabel", () => {
  it("returns full title when within word limit", () => {
    expect(shortNewsLinkLabel("AMD beats estimates")).toBe("AMD beats estimates")
  })

  it("truncates with ellipsis when over word limit", () => {
    expect(
      shortNewsLinkLabel("Advanced Micro Devices Is Up After New Partnership Targets Open")
    ).toBe("Advanced Micro Devices Is Up…")
  })

  it("normalizes whitespace", () => {
    expect(shortNewsLinkLabel("  one   two  ")).toBe("one two")
  })

  it("returns fallback for empty string", () => {
    expect(shortNewsLinkLabel("")).toBe("Read article")
    expect(shortNewsLinkLabel("   ")).toBe("Read article")
  })
})
