import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './providers/AuthProvider.jsx'
import { ThemeProvider } from './providers/ThemeProvider.jsx'
import { NotificationProvider } from './providers/NotificationProvider.jsx'

const queryClient = new QueryClient()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <NotificationProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </NotificationProvider>
      </QueryClientProvider>
    </ThemeProvider>
  </StrictMode>,
)
