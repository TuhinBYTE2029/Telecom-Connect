# Next Steps & Roadmap — Telecom Connect

**Current Milestone**: Phase 4 Completed (32 working endpoints, 58 tests passing, 93% test coverage).  
**Next Milestone**: Phase 5 — Authentication, Roles, Validation, Error Handling and Rate Limiting.

---

## Remaining Work for Phase 5 Onwards

### Phase 5: Authentication, Roles, Security & Rate Limiting
- **JWT Authentication System**:
  - `POST /api/v1/auth/login`: Issue access tokens using HS256 and secure password verification (bcrypt).
  - `GET /api/v1/auth/me`: Current authenticated user profile.
  - `POST /api/v1/auth/register`: Subscriber self-registration.
- **Role-Based Access Control (RBAC)**:
  - Role dependencies: `get_current_active_user`, `require_admin`, `require_staff_or_admin`, `require_subscriber_or_staff`.
  - Secure protected endpoints across circles, plans, subscribers, recharges, complaints, and plan changes.
- **Rate Limiting**:
  - Implement SlowAPI or Redis-backed rate limiting middleware per IP / token.
- **Security Hardening**:
  - Centralized CORS validation, request sanitization, and structured log masking verification.

### Phase 6: Unit & Integration Tests and Test Coverage
- Achieve comprehensive end-to-end integration testing for all role permissions, rate limits, and edge cases.
- Maintain >= 75% coverage (currently 93%).

### Phase 7: Redis Caching & Docker Compose
- Cache frequently requested prepaid plans and telecom circles with Redis TTL and cache invalidation on write.
- Multi-container `docker-compose.yml` with PostgreSQL, Redis, FastAPI app service, persistent volumes, and health checks.

### Phase 8: Minimal Frontend, Swagger & Postman Documentation
- Plain responsive HTML/CSS/JavaScript dashboard in `app/static/`.
- OpenAPI documentation enhancement with examples and tags.
- Postman Collection JSON export.

### Phase 9: k6 Load Testing & Final Documentation
- k6 performance script targeting 200 req/sec under 300ms latency (simulating IPL-season traffic).
- Architecture diagrams and final `README.md`.
