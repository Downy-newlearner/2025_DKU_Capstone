// src/api/auth.js
import axios from 'axios';
import config from '../config';

const API = axios.create({
  baseURL: config.api.baseURL,
  timeout: config.api.timeout,
  withCredentials: config.api.withCredentials,
});

export const signup = (data) => API.post('/sign-up', data, {
  headers: {
    "Content-Type": "application/json",
  },
});
export const login = (data) => API.post('/sign-in', data);
