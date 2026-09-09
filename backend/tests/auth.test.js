// backend/tests/auth.test.js
// NEW FILE
//
// Run with: npm test
// Covers Phase 1's exit criteria: "Write 5-10 backend tests for auth
// endpoints (signup, login, invalid password, duplicate email,
// protected route rejection)." Also covers the profile endpoint's
// server-side riskLambda derivation, since that's the other
// Phase-1-critical invariant (Phase 3's optimizer depends on it).

process.env.JWT_ACCESS_SECRET = process.env.JWT_ACCESS_SECRET || 'test_access_secret';
process.env.JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || 'test_refresh_secret';
process.env.MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/unused';

const request = require('supertest');
const {app} = require("../server");
const { installUserModelMock } = require('./helpers/mockUserModel');


const VALID_SIGNUP_BODY = {
  email: 'test@example.com',
  password: 'password123',
  capital: 10000000,
  timeHorizonYears: 5,
  riskLabel: 'moderate',
};

beforeEach(() => {
  // Fresh in-memory store for every test so tests don't leak state.
  installUserModelMock();
});

describe('POST /api/auth/signup', () => {
  test('creates a user and returns an access token + refresh cookie', async () => {
    const res = await request(app).post('/api/auth/signup').send(VALID_SIGNUP_BODY);

    expect(res.status).toBe(201);
    expect(res.body.accessToken).toEqual(expect.any(String));
    expect(res.body.user.email).toBe('test@example.com');
    expect(res.body.user.riskLabel).toBe('moderate');
    expect(res.body.user.riskLambda).toBe(2.5);
    expect(res.body.user).not.toHaveProperty('passwordHash');
    expect(res.headers['set-cookie']).toBeDefined();
    expect(res.headers['set-cookie'][0]).toMatch(/HttpOnly/);
  });

  test('rejects a weak password', async () => {
    const res = await request(app)
      .post('/api/auth/signup')
      .send({ ...VALID_SIGNUP_BODY, email: 'weakpw@example.com', password: '123' });

    expect(res.status).toBe(400);
    expect(res.body.errors.join(' ')).toMatch(/password/i);
  });

  test('rejects a malformed email', async () => {
    const res = await request(app)
      .post('/api/auth/signup')
      .send({ ...VALID_SIGNUP_BODY, email: 'not-an-email' });

    expect(res.status).toBe(400);
    expect(res.body.errors.join(' ')).toMatch(/email/i);
  });

  test('rejects a duplicate email', async () => {
    await request(app).post('/api/auth/signup').send(VALID_SIGNUP_BODY);
    const res = await request(app).post('/api/auth/signup').send(VALID_SIGNUP_BODY);

    expect(res.status).toBe(409);
  });

  test('rejects an invalid riskLabel', async () => {
    const res = await request(app)
      .post('/api/auth/signup')
      .send({ ...VALID_SIGNUP_BODY, email: 'badrisk@example.com', riskLabel: 'yolo' });

    expect(res.status).toBe(400);
    expect(res.body.errors.join(' ')).toMatch(/riskLabel/);
  });
});

describe('POST /api/auth/login', () => {
  test('logs in with correct credentials', async () => {
    await request(app).post('/api/auth/signup').send(VALID_SIGNUP_BODY);

    const res = await request(app)
      .post('/api/auth/login')
      .send({ email: VALID_SIGNUP_BODY.email, password: VALID_SIGNUP_BODY.password });

    expect(res.status).toBe(200);
    expect(res.body.accessToken).toEqual(expect.any(String));
  });

  test('rejects an incorrect password', async () => {
    await request(app).post('/api/auth/signup').send(VALID_SIGNUP_BODY);

    const res = await request(app)
      .post('/api/auth/login')
      .send({ email: VALID_SIGNUP_BODY.email, password: 'wrongpassword' });

    expect(res.status).toBe(401);
    expect(res.body.errors[0]).toMatch(/invalid email or password/i);
  });

  test('rejects a non-existent email with the same generic message (no user enumeration)', async () => {
    const res = await request(app)
      .post('/api/auth/login')
      .send({ email: 'nobody@example.com', password: 'password123' });

    expect(res.status).toBe(401);
    expect(res.body.errors[0]).toMatch(/invalid email or password/i);
  });
});

describe('Protected route rejection (GET /api/users/profile)', () => {
  test('rejects a request with no Authorization header', async () => {
    const res = await request(app).get('/api/users/profile');
    expect(res.status).toBe(401);
  });

  test('rejects a request with a malformed/invalid token', async () => {
    const res = await request(app)
      .get('/api/users/profile')
      .set('Authorization', 'Bearer not.a.real.token');
    expect(res.status).toBe(401);
  });

  test('accepts a request with a valid token and returns the profile', async () => {
    const signupRes = await request(app).post('/api/auth/signup').send(VALID_SIGNUP_BODY);
    const { accessToken } = signupRes.body;

    const res = await request(app)
      .get('/api/users/profile')
      .set('Authorization', `Bearer ${accessToken}`);

    expect(res.status).toBe(200);
    expect(res.body.user.email).toBe(VALID_SIGNUP_BODY.email);
    expect(res.body.user).not.toHaveProperty('passwordHash');
  });
});

describe('PUT /api/users/profile — riskLambda integrity', () => {
  test('recomputes riskLambda server-side when riskLabel changes', async () => {
    const signupRes = await request(app).post('/api/auth/signup').send(VALID_SIGNUP_BODY);
    const { accessToken } = signupRes.body;

    const res = await request(app)
      .put('/api/users/profile')
      .set('Authorization', `Bearer ${accessToken}`)
      .send({ riskLabel: 'aggressive' });

    expect(res.status).toBe(200);
    expect(res.body.user.riskLabel).toBe('aggressive');
    expect(res.body.user.riskLambda).toBe(1.2);
  });

  test('ignores a client-supplied riskLambda and always derives it from riskLabel', async () => {
    const signupRes = await request(app).post('/api/auth/signup').send(VALID_SIGNUP_BODY);
    const { accessToken } = signupRes.body;

    const res = await request(app)
      .put('/api/users/profile')
      .set('Authorization', `Bearer ${accessToken}`)
      .send({ riskLabel: 'conservative', riskLambda: 999 });

    expect(res.status).toBe(200);
    expect(res.body.user.riskLambda).toBe(4);
  });
});