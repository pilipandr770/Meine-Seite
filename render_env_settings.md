# Render Environment Variables for Database Optimization

When using Render with PostgreSQL, consider adding these environment variables to improve connection stability and performance:

## Connection Pool Settings

```
WEB_CONCURRENCY=4
SQLALCHEMY_POOL_SIZE=2
SQLALCHEMY_MAX_OVERFLOW=3
SQLALCHEMY_POOL_RECYCLE=180
SQLALCHEMY_POOL_TIMEOUT=15
```

### Explanation:

- `WEB_CONCURRENCY`: Sets the number of Gunicorn workers. For most web apps on Render, 4 is optimal.
- `SQLALCHEMY_POOL_SIZE`: Limits each worker to maintain 2 connections at most.
- `SQLALCHEMY_MAX_OVERFLOW`: Allows 3 additional temp connections if needed.
- `SQLALCHEMY_POOL_RECYCLE`: Recycles connections after 3 minutes (180s).
- `SQLALCHEMY_POOL_TIMEOUT`: Fail after 15s if can't get a connection.

## SSL Settings (for pg8000)

```
PGSSLMODE=require
```

### Additional Recommendations

1. Set up health checks to monitor your application:
   - Add a health check URL to `/health`
   - Configure Render to use this endpoint for health checks

2. Consider adding connection retries for critical operations.

3. Always implement transaction timeouts to prevent long-running transactions.

4. Set appropriate timeouts for all external services.

To apply these settings, go to your Render dashboard, navigate to your service, click "Environment" and add these variables.
