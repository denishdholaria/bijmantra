/**
 * Commercial Dashboard
 *
 * Seed traceability, licensing, DUS testing, and business operations.
 */

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ClipboardCheck,
  Sprout,
  FileText,
  DollarSign,
  ArrowRight,
  CheckCircle2,
  Clock,
  TrendingUp,
  Building2,
} from 'lucide-react';

import { apiClient } from '@/lib/api-client';

export function Dashboard() {
  // Fetch DUS stats
  const { data: dusStats } = useQuery({
    queryKey: ['dus-stats'],
    queryFn: async () => {
      try {
        // Use apiClient for DUS stats
        // Service returns { trials: [], total: number }
        const res = await apiClient.dusService.getTrials();
        const trials = res.trials || [];
        return {
          total: res.total || trials.length,
          active: trials.filter((t: any) => t.status === 'in_progress').length,
        };
      } catch (err) {
        console.error('Failed to fetch DUS stats:', err);
        return { total: 0, active: 0 };
      }
    },
  });

  // Fetch licensing stats
  const { data: licensingStats } = useQuery({
    queryKey: ['licensing-stats'],
    queryFn: async () => {
      try {
        const [varietiesRes, licensesRes] = await Promise.all([
          apiClient.licensingService.getLicensingVarieties(),
          apiClient.licensingService.getLicenses(),
        ]);
        
        // Unpack service responses: { status: 'success', data: [], count: n }
        const varieties = varietiesRes.data || [];
        const agreements = licensesRes.data || [];
        
        return {
          varieties: varieties.length,
          protected: varieties.filter((v: any) => v.protection_status === 'granted').length,
          agreements: agreements.length,
          active: agreements.filter((a: any) => a.status === 'active').length,
        };
      } catch (err) {
        console.error('Failed to fetch licensing stats:', err);
        return { varieties: 0, protected: 0, agreements: 0, active: 0 };
      }
    },
  });

  const modules = [
    {
      icon: ClipboardCheck,
      title: 'DUS Testing',
      description: 'UPOV variety protection with 10 crop templates',
      href: '/commercial/dus',
      color: 'bg-purple-100 text-purple-600',
      stats: dusStats ? `${dusStats.total} trials` : 'Loading...',
      badge: 'Active',
    },
    {
      icon: Sprout,
      title: 'Variety Registration',
      description: 'Register and protect plant varieties',
      href: '/seed-operations/varieties',
      color: 'bg-green-100 text-green-600',
      stats: licensingStats ? `${licensingStats.varieties} varieties` : 'Loading...',
      badge: 'Active',
    },
    {
      icon: FileText,
      title: 'License Agreements',
      description: 'Manage licensing contracts and territories',
      href: '/seed-operations/agreements',
      color: 'bg-blue-100 text-blue-600',
      stats: licensingStats ? `${licensingStats.agreements} agreements` : 'Loading...',
      badge: 'Active',
    },

  ];

  const quickActions = [
    { label: 'New DUS Trial', href: '/commercial/dus', icon: ClipboardCheck },
    { label: 'Register Variety', href: '/seed-operations/varieties', icon: Sprout },
    { label: 'New Agreement', href: '/seed-operations/agreements', icon: FileText },

  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Building2 className="h-7 w-7 text-indigo-600" />
          Commercial Division
        </h1>
        <p className="text-muted-foreground">
          DUS testing, variety protection, licensing, and royalty management
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <ClipboardCheck className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{dusStats?.total || 0}</p>
                <p className="text-xs text-muted-foreground">DUS Trials</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{licensingStats?.protected || 0}</p>
                <p className="text-xs text-muted-foreground">Protected Varieties</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileText className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{licensingStats?.active || 0}</p>
                <p className="text-xs text-muted-foreground">Active Licenses</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">10</p>
                <p className="text-xs text-muted-foreground">Crop Templates</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 flex-wrap">
            {quickActions.map((action) => (
              <Button key={action.label} variant="outline" size="sm" asChild>
                <Link to={action.href}>
                  <action.icon className="h-4 w-4 mr-2" />
                  {action.label}
                </Link>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Module Cards */}
      <div className="grid md:grid-cols-2 gap-4">
        {modules.map((module) => (
          <Card key={module.title} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${module.color}`}>
                    <module.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium">{module.title}</h3>
                      <Badge variant="outline" className="text-xs bg-green-50 text-green-700">
                        {module.badge}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">{module.description}</p>
                    <p className="text-xs text-muted-foreground mt-2">{module.stats}</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" asChild>
                  <Link to={module.href}>
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* DUS Crop Templates */}
      <Card>
        <CardHeader>
          <CardTitle>DUS Crop Templates</CardTitle>
          <CardDescription>
            UPOV-compliant character templates for variety testing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-2">
            {[
              { name: 'Rice', chars: 20 },
              { name: 'Wheat', chars: 15 },
              { name: 'Maize', chars: 18 },
              { name: 'Cotton', chars: 18 },
              { name: 'Castor', chars: 15 },
              { name: 'Groundnut', chars: 17 },
              { name: 'Cumin', chars: 14 },
              { name: 'Pigeonpea', chars: 16 },
              { name: 'Soybean', chars: 15 },
              { name: 'Chickpea', chars: 16 },
            ].map((crop) => (
              <div
                key={crop.name}
                className="p-2 border rounded text-center hover:bg-muted/50 cursor-pointer"
              >
                <p className="font-medium text-sm">{crop.name}</p>
                <p className="text-xs text-muted-foreground">{crop.chars} chars</p>
              </div>
            ))}
          </div>
          <div className="mt-4">
            <Button variant="outline" size="sm" asChild>
              <Link to="/commercial/dus/crops">
                View All Templates
                <ArrowRight className="h-4 w-4 ml-2" />
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Upcoming Features */}
      <Card>
        <CardHeader>
          <CardTitle>Coming Soon</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="flex items-center gap-3 p-3 border rounded-lg">
              <Clock className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="font-medium">Blockchain Certification</p>
                <p className="text-sm text-muted-foreground">Immutable seed certification records</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 border rounded-lg">
              <Clock className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="font-medium">ERPNext Integration</p>
                <p className="text-sm text-muted-foreground">Sync with inventory and sales</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default Dashboard;
