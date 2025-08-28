import * as React from 'react'

export type Toast = {
  id: string
  title?: string
  description?: string
  variant?: 'default' | 'destructive'
  duration?: number
}

const ToastContext = React.createContext<{
  toasts: Toast[]
  toast: (t: Omit<Toast, 'id'>) => void
  remove: (id: string) => void
} | null>(null)

function uid() {
  return Math.random().toString(36).slice(2)
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([])

  const remove = React.useCallback((id: string) => {
    setToasts((ts) => ts.filter((t) => t.id !== id))
  }, [])

  const toast = React.useCallback((t: Omit<Toast, 'id'>) => {
    const id = uid()
    const duration = typeof t.duration === 'number' ? t.duration : 2500
    setToasts((ts) => [...ts, { id, ...t }])
    if (duration > 0) {
      setTimeout(() => remove(id), duration)
    }
  }, [remove])

  return (
    <ToastContext.Provider value={{ toasts, toast, remove }}>
      {children}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 space-y-2" style={{ zIndex: 100000 }}>
        {toasts.map((t) => (
          <div key={t.id} className={`rounded-md shadow px-4 py-2 text-sm text-center ${t.variant === 'destructive' ? 'bg-red-600 text-white' : 'bg-gray-800 text-white'}`}>
            {t.title && <div className="font-semibold">{t.title}</div>}
            {t.description && <div className="opacity-90">{t.description}</div>}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = React.useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within a ToastProvider')
  return { toast: ctx.toast }
}

