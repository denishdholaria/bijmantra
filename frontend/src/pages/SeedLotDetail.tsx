/**
 * Seed Lot Detail Page
 * BrAPI v2.1 Germplasm Module
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'

// Transaction interface
interface Transaction {
  id: string;
  type: string;
  amount: number;
  reason: string;
  date: string;
  user: string;
  reference?: string;
  balance?: number;
}

function TransactionHistory({ seedLotId, units }: { seedLotId: string; units: string }) {
  // Fetch transactions from API
  const { data: transactions = [], isLoading } = useQuery({
    queryKey: ['seedlot-transactions', seedLotId],
    queryFn: async (): Promise<Transaction[]> => {
      try {
        const response = await apiClient.getSeedlotTransactionsById(seedLotId, { pageSize: 100 });
        const brapiData = response.result?.data || [];

        return brapiData.map((txn: any) => ({
          id: txn.transactionDbId,
          // Determine type based on amount
          type: txn.amount >= 0 ? 'addition' : 'removal',
          amount: txn.amount,
          reason: txn.transactionDescription || 'Manual Transaction',
          date: txn.transactionTimestamp,
          user: txn.additionalInfo?.user_name || 'System',
          reference: txn.externalReferences ? Object.values(txn.externalReferences).join(', ') : undefined,
        }));
      } catch (error) {
        console.error('Failed to fetch transactions:', error);
      }
      return [];
    },
  });
  
  const typeIcons: Record<string, string> = {
    addition: '➕',
    removal: '➖',
    transfer_in: '📥',
    transfer_out: '📤',
    adjustment: '🔧',
    harvest: '🌾',
  };
  
  const typeColors: Record<string, string> = {
    addition: 'text-green-600',
    removal: 'text-red-600',
    transfer_in: 'text-blue-600',
    transfer_out: 'text-orange-600',
    adjustment: 'text-purple-600',
    harvest: 'text-green-600',
  };

  if (isLoading) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        <div className="animate-spin text-4xl mb-2">⏳</div>
        <p>Loading transactions...</p>
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        <div className="text-4xl mb-2">📋</div>
        <p>No transactions recorded yet</p>
      </div>
    );
  }

  // Calculate running balance
  let runningBalance = 0;
  const transactionsWithBalance = [...transactions].reverse().map(t => {
    runningBalance += t.amount;
    return { ...t, balance: runningBalance };
  }).reverse();

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 p-4 bg-muted/50 rounded-lg">
        <div className="text-center">
          <p className="text-2xl font-bold text-green-600">
            +{transactions.filter(t => t.amount > 0).reduce((sum, t) => sum + t.amount, 0)}
          </p>
          <p className="text-xs text-muted-foreground">Total In</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-red-600">
            {transactions.filter(t => t.amount < 0).reduce((sum, t) => sum + t.amount, 0)}
          </p>
          <p className="text-xs text-muted-foreground">Total Out</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold">{transactions.length}</p>
          <p className="text-xs text-muted-foreground">Transactions</p>
        </div>
      </div>

      {/* Transaction List */}
      <div className="border rounded-lg divide-y max-h-[400px] overflow-y-auto">
        {transactionsWithBalance.map((txn) => (
          <div key={txn.id} className="p-3 hover:bg-muted/30 flex items-center gap-4">
            <div className="text-2xl">{typeIcons[txn.type]}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium capitalize">{txn.type.replace('_', ' ')}</span>
                {txn.reference && (
                  <Badge variant="outline" className="text-xs">{txn.reference}</Badge>
                )}
              </div>
              <p className="text-sm text-muted-foreground">{txn.reason}</p>
              <p className="text-xs text-muted-foreground">
                {new Date(txn.date).toLocaleDateString()} • {txn.user}
              </p>
            </div>
            <div className="text-right">
              <p className={`font-bold ${typeColors[txn.type]}`}>
                {txn.amount > 0 ? '+' : ''}{txn.amount} {units}
              </p>
              <p className="text-xs text-muted-foreground">
                Balance: {txn.balance} {units}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function SeedLotDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDelete, setShowDelete] = useState(false)
  const [transactionAmount, setTransactionAmount] = useState('')
  const [transactionType, setTransactionType] = useState<'add' | 'remove' | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['seedlot', id],
    queryFn: () => apiClient.getSeedLot(id!),
    enabled: !!id,
  })

  const { data: germplasmData } = useQuery({
    queryKey: ['germplasm', data?.result?.germplasmDbId],
    queryFn: () => apiClient.getGermplasmById(data!.result.germplasmDbId),
    enabled: !!data?.result?.germplasmDbId,
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteSeedLot(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seedlots'] })
      toast.success('Seed lot deleted')
      navigate('/seedlots')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Delete failed'),
  })

  const transactionMutation = useMutation({
    mutationFn: async (data: { amount: number; type: 'add' | 'remove' }) => {
      const finalAmount = data.type === 'add' ? data.amount : -data.amount;
      return apiClient.createSeedlotTransaction({
        seedLotDbId: seedLot?.seedLotDbId,
        amount: finalAmount,
        transactionDescription: data.type === 'add' ? 'Manual stock addition' : 'Manual stock removal',
        transactionTimestamp: new Date().toISOString(),
        units: seedLot?.units || 'units'
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seedlot', id] })
      queryClient.invalidateQueries({ queryKey: ['seedlot-transactions', seedLot?.seedLotDbId] })
      toast.success('Transaction record added')
      setTransactionType(null)
      setTransactionAmount('')
    },
    onError: (error) => {
      console.error(error);
      toast.error('Failed to record transaction');
    }
  })

  const seedLot = data?.result
  const germplasm = germplasmData?.result

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error || !seedLot) {
    return (
      <div className="max-w-4xl mx-auto p-12 text-center">
        <div className="text-6xl mb-4">⚠️</div>
        <h2 className="text-xl font-bold mb-2">Seed Lot Not Found</h2>
        <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Could not load seed lot'}</p>
        <Button asChild><Link to="/seedlots">← Back to Seed Lots</Link></Button>
      </div>
    )
  }

  const stockStatus = seedLot.amount > 100 ? 'good' : seedLot.amount > 0 ? 'low' : 'empty'

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild aria-label="Back to seed lots"><Link to="/seedlots">←</Link></Button>
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">{seedLot.seedLotName || seedLot.seedLotDbId}</h1>
            <p className="text-muted-foreground">Seed Lot</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild><Link to={`/seedlots/${id}/edit`}>✏️ Edit</Link></Button>
          <Button variant="destructive" onClick={() => setShowDelete(true)}>🗑️ Delete</Button>
        </div>
      </div>

      {/* Stock Status Card */}
      <Card className={stockStatus === 'good' ? 'border-green-200 bg-green-50/50' : stockStatus === 'low' ? 'border-orange-200 bg-orange-50/50' : 'border-red-200 bg-red-50/50'}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Current Stock</p>
              <p className="text-4xl font-bold">{seedLot.amount || 0} <span className="text-lg font-normal">{seedLot.units || 'units'}</span></p>
            </div>
            <Badge variant={stockStatus === 'good' ? 'default' : stockStatus === 'low' ? 'secondary' : 'destructive'} className="text-lg px-4 py-2">
              {stockStatus === 'good' ? '✓ In Stock' : stockStatus === 'low' ? '⚠ Low Stock' : '✗ Empty'}
            </Badge>
          </div>
          <div className="flex gap-2 mt-4">
            <Button size="sm" variant="outline" onClick={() => setTransactionType('add')}>➕ Add Stock</Button>
            <Button size="sm" variant="outline" onClick={() => setTransactionType('remove')}>➖ Remove Stock</Button>
          </div>
        </CardContent>
      </Card>

      {/* Transaction Dialog */}
      {transactionType && (
        <Card className="border-primary">
          <CardHeader>
            <CardTitle>{transactionType === 'add' ? '➕ Add Stock' : '➖ Remove Stock'}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Amount ({seedLot.units || 'units'})</Label>
              <Input type="number" value={transactionAmount} onChange={(e) => setTransactionAmount(e.target.value)} placeholder="Enter amount..." />
            </div>
            <div className="flex gap-2">
              <Button onClick={() => transactionMutation.mutate({ amount: parseFloat(transactionAmount), type: transactionType })} disabled={!transactionAmount}>
                Confirm {transactionType === 'add' ? 'Addition' : 'Removal'}
              </Button>
              <Button variant="outline" onClick={() => setTransactionType(null)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Details */}
        <Card>
          <CardHeader>
            <CardTitle>Lot Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Lot ID</p>
                <p className="font-mono">{seedLot.seedLotDbId}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Created Date</p>
                <p>{seedLot.createdDate?.split('T')[0] || '-'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Storage Location</p>
                <p>{seedLot.storageLocation || '-'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Source</p>
                <p>{seedLot.sourceCollection || '-'}</p>
              </div>
            </div>
            {seedLot.seedLotDescription && (
              <div>
                <p className="text-muted-foreground text-sm">Description</p>
                <p className="text-sm">{seedLot.seedLotDescription}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Germplasm Info */}
        <Card>
          <CardHeader>
            <CardTitle>Germplasm</CardTitle>
          </CardHeader>
          <CardContent>
            {germplasm ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">🌱</span>
                  <div>
                    <Link to={`/germplasm/${germplasm.germplasmDbId}`} className="font-semibold text-primary hover:underline">
                      {germplasm.germplasmName}
                    </Link>
                    <p className="text-sm text-muted-foreground">{germplasm.accessionNumber || germplasm.germplasmDbId}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-muted-foreground">Species</p>
                    <p className="italic">{germplasm.species || '-'}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Genus</p>
                    <p className="italic">{germplasm.genus || '-'}</p>
                  </div>
                </div>
              </div>
            ) : seedLot.germplasmDbId ? (
              <p className="text-muted-foreground">Loading germplasm...</p>
            ) : (
              <p className="text-muted-foreground">No germplasm linked</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Transaction History */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
          <CardDescription>Stock movements for this seed lot</CardDescription>
        </CardHeader>
        <CardContent>
          <TransactionHistory seedLotId={seedLot.seedLotDbId} units={seedLot.units || 'units'} />
        </CardContent>
      </Card>

      <ConfirmDialog
        isOpen={showDelete}
        onClose={() => setShowDelete(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete Seed Lot"
        message="Are you sure you want to delete this seed lot? This action cannot be undone."
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
