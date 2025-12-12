const ACCESS_TOKEN_KEY = 'contractorchat.access';
const REFRESH_TOKEN_KEY = 'contractorchat.refresh';

export const authStorage = {
  getAccessToken() {
    return window.localStorage.getItem(ACCESS_TOKEN_KEY);
  },
  setAccessToken(token) {
    if (!token) {
      window.localStorage.removeItem(ACCESS_TOKEN_KEY);
      return;
    }
    window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
  },
  getRefreshToken() {
    return window.localStorage.getItem(REFRESH_TOKEN_KEY);
  },
  setRefreshToken(token) {
    if (!token) {
      window.localStorage.removeItem(REFRESH_TOKEN_KEY);
      return;
    }
    window.localStorage.setItem(REFRESH_TOKEN_KEY, token);
  },
  clear() {
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

