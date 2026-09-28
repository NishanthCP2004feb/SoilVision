import { describe, it, expect, beforeEach } from 'vitest';
import { session } from './api';

describe('session', () => {
  beforeEach(() => { session.clear(); });
  it('stores and retrieves token', () => {
    session.set('test-token');
    expect(session.get()).toBe('test-token');
  });
  it('clears token', () => {
    session.set('test-token');
    session.clear();
    expect(session.get()).toBe('');
  });
});
