/**
 * Regeneration Planning Page
 * 
 * Plan and track seed regeneration activities for maintaining viability.
 */

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface RegenerationTask {
  id: string;
  accessionNumber: string;
  species: string;
  reason: 'low-viability' | 'low-quantity' | 'scheduled';
  priority: 'high' | 'medium' | 'low';
  currentViability: number;
  currentQuantity: number;
  targetQuantity: number;
  plannedSeason: string;
  status: 'planned' | 'in-progress' | 'harvested' | 'completed';
  location?: string;
}

export function RegenerationPlanning() {
  const { data: tasks } = useQuery<RegenerationTask[]>({
    queryKey: ['seed-bank', 'regeneration-tasks'],
    queryFn: async () => [
      { id: '1', accessionNumber: 'ACC-2019-0456', species: 'Oryza rufipogon', reason: 'low-viability', priority: 'high', currentViability: 45, currentQuantity: 200, targetQuantity: 5000, plannedSeason: 'Kharif 2025', status: 'planned' },
      { id: '2', accessionNumber: 'ACC-2018-0234', species: 'Triticum dicoccoides', reason: 'low-quantity', priority: 'high', currentViability: 82, currentQuantity: 150, targetQuantity: 3000, plannedSeason: 'Rabi 2024-25', status: 'in-progress', location: 'Field Block A' },
      { id: '3', accessionNumber: 'ACC-2020-0789', species: 'Zea mays', reason: 'scheduled', priority: 'medium', currentViability: 78, currentQuantity: 800, targetQuantity: 5000, plannedSeason: 'Kharif 2025', status: 'planned' },
      { id: '4', accessionNumber: 'ACC-2017-0123', species: 'Glycine max', reason: 'low-viability', priority: 'medium', currentViability: 68, currentQuantity: 500, targetQuantity: 4000, plannedSeason: 'Kharif 2025', status: 'planned' },
    ],
  });

  const getPriorityBadge = (priority: string) => {
    const styles: Record<string, string> = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800',
    };
    return styles[priority] || 'bg-gray-100 text-gray-800';
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      planned: 'bg-blue-100 text-blue-800',
      'in-progress': 'bg-purple-100 text-purple-800',
      harvested: 'bg-orange-100 text-orange-800',
      completed: 'bg-green-100 text-green-800',
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  const getReasonIcon = (reason: string) => {
    switch (reason) {
      case 'low-viability': return '⚠️';
      case 'low-quantity': return '📉';
      case 'scheduled': return '📅';
      default: return '📋';
    }
  };

  const highPriorityCount = tasks?.filter(t => t.priority === 'high').length || 0;
  const inProgressCount = tasks?.filter(t => t.status === 'in-progress').length || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Regeneration Planning</h1>
          <p className="text-gray-600 mt-1">Plan and track seed regeneration activities</p>
        </div>
        <Button>🌱 Plan Regeneration</Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-red-600">{highPriorityCount}</div>
            <div className="text-sm text-gray-500">High Priority</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">{inProgressCount}</div>
            <div className="text-sm text-gray-500">In Progress</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{tasks?.length || 0}</div>
            <div className="text-sm text-gray-500">Total Planned</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">12</div>
            <div className="text-sm text-gray-500">Completed YTD</div>
          </CardContent>
        </Card>
      </div>

      {/* Tasks Table */}
      <Card>
        <CardHeader>
          <CardTitle>Regeneration Queue</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Accession</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Species</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Reason</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Priority</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Viability</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Qty</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Season</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {tasks?.map((task) => (
                  <tr key={task.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-sm text-green-600">{task.accessionNumber}</td>
                    <td className="px-4 py-3 italic text-gray-700">{task.species}</td>
                    <td className="px-4 py-3 text-center">
                      <span title={task.reason}>{getReasonIcon(task.reason)}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityBadge(task.priority)}`}>
                        {task.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-medium">{task.currentViability}%</td>
                    <td className="px-4 py-3 text-right font-mono text-sm">{task.currentQuantity}</td>
                    <td className="px-4 py-3 text-sm">{task.plannedSeason}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(task.status)}`}>
                        {task.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="outline" size="sm">Manage</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default RegenerationPlanning;
