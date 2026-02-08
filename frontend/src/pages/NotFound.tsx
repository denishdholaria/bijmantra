/**
 * 404 Not Found Page
 */

import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

export function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-gray-50 to-green-50/30">
      <Card className="max-w-md w-full">
        <CardContent className="p-8 text-center">
          <div className="text-8xl mb-4">🌱</div>
          <h1 className="text-4xl font-bold mb-2">404</h1>
          <h2 className="text-xl font-semibold mb-4">Page Not Found</h2>
          <p className="text-muted-foreground mb-6">
            The page you're looking for doesn't exist or has been moved.
          </p>
          <div className="flex gap-4 justify-center">
            <Button asChild>
              <Link to="/dashboard">Go to Dashboard</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/search">Search</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
