# API Design Rules: REST API Conventions

## REST API Principles

### 1. RESTful Conventions
- **Resources**: Use nouns, not verbs in URLs (`/stocks`, not `/getStocks`)
- **HTTP Methods**: Use appropriate HTTP methods:
  - `GET`: Retrieve resources
  - `POST`: Create new resources
  - `PUT`: Replace entire resource
  - `PATCH`: Partial update
  - `DELETE`: Delete resource
- **Idempotency**: GET, PUT, DELETE should be idempotent
- **Stateless**: Each request contains all information needed

### 2. URL Structure
```
/api/v1/{resource}/{id}/{sub-resource}/{sub-id}
```

**Examples:**
- `GET /api/v1/stocks` - List all stocks
- `GET /api/v1/stocks/AAPL` - Get specific stock
- `POST /api/v1/stocks` - Create stock
- `PUT /api/v1/stocks/AAPL` - Update stock
- `DELETE /api/v1/stocks/AAPL` - Delete stock
- `GET /api/v1/stocks/AAPL/history` - Get stock history (sub-resource)

### 3. API Versioning
- **Always version**: All APIs must be versioned (`/api/v1/`, `/api/v2/`)
- **Version in URL**: Include version in URL path, not headers
- **Backward Compatibility**: Maintain backward compatibility within version
- **Deprecation**: Announce deprecations before removing endpoints

## Request Design

### 4. Query Parameters
- **Filtering**: Use query params for filtering (`?symbol=AAPL&exchange=NASDAQ`)
- **Pagination**: Use `page` and `limit` or `offset` and `limit`
- **Sorting**: Use `sort` parameter (`?sort=price:desc`)
- **Search**: Use `q` or `search` for search queries

```python
# Example endpoint
@router.get("/stocks")
async def get_stocks(
    symbol: Optional[str] = None,
    exchange: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: Optional[str] = None
):
    pass
```

### 5. Request Body
- **Content-Type**: Always `application/json`
- **Validation**: Validate all request bodies with Pydantic
- **Required Fields**: Mark required fields explicitly
- **Nested Objects**: Use nested Pydantic models for complex structures

```python
class StockCreateRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1)
    exchange: str
    sector: Optional[str] = None
```

### 6. Headers
- **Authorization**: `Authorization: Bearer <token>`
- **Content-Type**: `Content-Type: application/json`
- **Accept**: `Accept: application/json` (optional)
- **Custom Headers**: Use `X-` prefix for custom headers

## Response Design

### 7. Response Structure
**Success Response:**
```json
{
  "data": {
    // Resource data
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "v1"
  }
}
```

**List Response:**
```json
{
  "data": [
    // Array of resources
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

**Error Response:**
```json
{
  "error": {
    "code": "STOCK_NOT_FOUND",
    "message": "Stock with symbol AAPL not found",
    "details": {
      "symbol": "AAPL"
    }
  }
}
```

### 8. HTTP Status Codes
- **200 OK**: Successful GET, PUT, PATCH
- **201 Created**: Successful POST (resource created)
- **204 No Content**: Successful DELETE
- **400 Bad Request**: Invalid request (validation errors)
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Authenticated but not authorized
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (e.g., duplicate)
- **422 Unprocessable Entity**: Validation errors
- **500 Internal Server Error**: Server error

### 9. Error Response Format
```python
class ErrorResponse(BaseModel):
    error: ErrorDetail

class ErrorDetail(BaseModel):
    code: str  # Machine-readable error code
    message: str  # Human-readable message
    details: Optional[Dict[str, Any]] = None  # Additional context
```

**Error Codes:**
- `VALIDATION_ERROR`: Input validation failed
- `RESOURCE_NOT_FOUND`: Resource doesn't exist
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `DUPLICATE_RESOURCE`: Resource already exists
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

## Pagination

### 10. Pagination Patterns
**Offset-based:**
```
GET /api/v1/stocks?offset=0&limit=20
```

**Cursor-based (for large datasets):**
```
GET /api/v1/stocks?cursor=abc123&limit=20
```

**Response:**
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "hasMore": true,
    "nextCursor": "xyz789"
  }
}
```

## Filtering and Sorting

### 11. Filtering Rules
- **Query Parameters**: Use query params for filters
- **Multiple Filters**: Combine with `&` (`?symbol=AAPL&exchange=NASDAQ`)
- **Operators**: Support common operators (`?price__gte=100&price__lte=200`)
- **Documentation**: Document all filter options in OpenAPI

### 12. Sorting Rules
- **Sort Parameter**: Use `sort` query parameter
- **Format**: `sort=field:direction` (`sort=price:desc`)
- **Multiple Fields**: `sort=price:desc,name:asc`
- **Default**: Always have a default sort order

## Rate Limiting

### 13. Rate Limiting Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### 14. Rate Limit Response
When rate limit exceeded (429):
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again later.",
    "details": {
      "limit": 100,
      "remaining": 0,
      "resetAt": "2024-01-01T01:00:00Z"
    }
  }
}
```

## API Documentation

### 15. OpenAPI/Swagger
- **Auto-Generation**: Use FastAPI's automatic OpenAPI generation
- **Descriptions**: Add descriptions to all endpoints and models
- **Examples**: Include request/response examples
- **Tags**: Organize endpoints with tags

```python
@router.post(
    "/stocks",
    response_model=StockResponse,
    status_code=201,
    summary="Create a new stock",
    description="Creates a new stock entry in the system",
    tags=["stocks"]
)
async def create_stock(request: StockCreateRequest):
    """
    Create a new stock.
    
    - **symbol**: Stock symbol (required, 1-10 characters)
    - **name**: Stock name (required)
    - **exchange**: Stock exchange (required)
    """
    pass
```

### 16. Response Models
- **Always Define**: Define response models for all endpoints
- **Consistent**: Use consistent response structure
- **Nested Models**: Use nested models for complex responses

## Security

### 17. Authentication
- **JWT Tokens**: Use JWT for authentication
- **Bearer Token**: Use `Authorization: Bearer <token>` header
- **Token Validation**: Validate tokens on protected endpoints
- **Refresh Tokens**: Implement refresh token mechanism

### 18. Authorization
- **Role-Based**: Implement role-based access control (RBAC)
- **Resource-Level**: Check permissions at resource level
- **Error Messages**: Don't reveal existence of resources in 403 errors

### 19. Input Validation
- **Pydantic**: Use Pydantic for all input validation
- **Sanitization**: Sanitize all user inputs
- **Type Validation**: Validate types strictly
- **Length Limits**: Set appropriate length limits

## Performance

### 20. Caching Headers
```
Cache-Control: public, max-age=3600
ETag: "abc123"
Last-Modified: Wed, 01 Jan 2024 00:00:00 GMT
```

### 21. Response Compression
- **Gzip**: Enable gzip compression for responses
- **Content-Encoding**: Set appropriate Content-Encoding header

### 22. Database Optimization
- **Eager Loading**: Load related data efficiently
- **Pagination**: Always paginate list endpoints
- **Indexes**: Use database indexes for query optimization
- **Query Optimization**: Profile and optimize slow queries

## Testing

### 23. API Testing
- **Test All Endpoints**: Test all endpoints
- **Test Status Codes**: Verify correct status codes
- **Test Validation**: Test input validation
- **Test Errors**: Test error responses

### 24. API Contract Testing
- **Schema Validation**: Validate request/response schemas
- **Version Testing**: Test API versioning
- **Backward Compatibility**: Test backward compatibility

## Key Rules Summary

1. **Always** version APIs (`/api/v1/`)
2. **Use** RESTful conventions (nouns, HTTP methods)
3. **Validate** all inputs with Pydantic
4. **Return** consistent response structure
5. **Use** appropriate HTTP status codes
6. **Document** all endpoints with OpenAPI
7. **Paginate** all list endpoints
8. **Handle** errors consistently
9. **Secure** all endpoints (auth, validation)
10. **Optimize** for performance (caching, compression)
