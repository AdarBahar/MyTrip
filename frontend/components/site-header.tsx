"use client"

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Menu } from 'lucide-react'

export function SiteHeader() {
  const router = useRouter()
  const [displayName, setDisplayName] = useState<string>('')

  useEffect(() => {
    try {
      const raw = localStorage.getItem('user_data')
      if (raw) {
        const u = JSON.parse(raw)
        setDisplayName(u?.display_name || u?.email || 'User')
      }
    } catch {}
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
    router.push('/login')
  }

  return (
    <header className="w-full bg-white/80 backdrop-blur border-b border-gray-200">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/" className="text-lg font-semibold tracking-tight text-gray-900">Road Trip planner</Link>
        <div className="flex items-center gap-3">
          {displayName && <span className="text-sm text-gray-700 hidden sm:inline">{displayName}</span>}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon" aria-label="Open menu">
                <Menu className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => router.push('/settings/user')}>User Settings</DropdownMenuItem>
              <DropdownMenuItem onClick={() => router.push('/settings/app')}>App Settings</DropdownMenuItem>
              <DropdownMenuItem onClick={() => router.push('/about')}>About</DropdownMenuItem>
              <DropdownMenuItem onClick={handleLogout}>Log out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}

