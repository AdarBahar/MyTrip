'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/use-toast'
import { getUserSettings, updateUserSettings } from '@/lib/api/settings'

export default function AppSettingsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCountrySuffix, setShowCountrySuffix] = useState<boolean>(false)
  const { toast } = useToast()

  useEffect(() => {
    (async () => {
      try {
        const s = await getUserSettings()
        setShowCountrySuffix(!!s.show_country_suffix)
      } catch (e) {
        setError('Failed to load settings')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const handleSave = async () => {
    try {
      await updateUserSettings({ show_country_suffix: showCountrySuffix })
      toast({ title: 'Settings saved', description: `Show country in addresses ${showCountrySuffix ? 'enabled' : 'disabled'}.`, duration: 2000 })
    } catch {
      toast({ title: 'Failed to save settings', description: 'Please try again.', variant: 'destructive' })
    }
  }

  if (loading) return <div className="container mx-auto px-4 py-8">Loading...</div>
  if (error) return <div className="container mx-auto px-4 py-8 text-red-600">{error}</div>

  return (
    <div className="container mx-auto px-4 py-8">
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>App Settings</CardTitle>
          <CardDescription>Configure how the app behaves for your account</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={showCountrySuffix}
                onChange={(e) => setShowCountrySuffix(e.target.checked)}
              />
              <div>
                <div className="font-medium">Show country in addresses</div>
                <div className="text-sm text-gray-500">When on, append country for non-US addresses in day Start/End lines.</div>
              </div>
            </label>
          </div>

          <div>
            <Button onClick={handleSave}>Save changes</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

