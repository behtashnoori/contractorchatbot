# Frontend - سامانه فاکتور

این پروژه با React + Vite ساخته شده است.

## تنظیمات API

سیستم به صورت خودکار آدرس API را تشخیص می‌دهد:

### حالت‌های مختلف:

1. **Localhost (توسعه محلی)**
   - اگر از `localhost:6902` یا `127.0.0.1:6902` استفاده کنید
   - API به صورت خودکار به `http://localhost:8000` متصل می‌شود

2. **دسترسی از شبکه (تست)**
   - اگر از IP آدرس (مثلاً `http://192.168.1.100:6902`) استفاده کنید
   - API به صورت خودکار به `http://192.168.1.100:8000` متصل می‌شود
   - **نکته**: مطمئن شوید backend هم روی `0.0.0.0:8000` اجرا شود

3. **Production (سرور مشتری)**
   - یک فایل `.env` در پوشه `frontend` ایجاد کنید:
   ```env
   VITE_API_BASE_URL=http://your-server-ip:8000
   ```
   - یا برای HTTPS:
   ```env
   VITE_API_BASE_URL=https://api.yourdomain.com
   ```

## اجرای پروژه

```bash
npm install
npm run dev
```

سرور روی `http://localhost:6902` (یا IP شما در شبکه) اجرا می‌شود.

---

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
