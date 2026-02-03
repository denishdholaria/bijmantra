import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import {
  Languages,
  Globe,
  Check,
  Search,
  Download,
  Upload,
  RefreshCw,
  Settings,
  BookOpen,
  MessageSquare
} from 'lucide-react'

export function LanguageSettings() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedLanguage, setSelectedLanguage] = useState('en')
  const queryClient = useQueryClient()

  // Fetch languages
  const { data: languagesData, isLoading: languagesLoading } = useQuery({
    queryKey: ['languages'],
    queryFn: () => apiClient.languageService.listLanguages(),
  })

  const languages = languagesData?.data || []

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['language-stats'],
    queryFn: () => apiClient.languageService.getStats(),
  })

  const stats = statsData?.data

  // Fetch translation keys
  const { data: keysData } = useQuery({
    queryKey: ['translation-keys'],
    queryFn: () => apiClient.languageService.listTranslationKeys({ limit: 10 }),
  })

  const translationKeys = keysData?.data || []

  // Update language mutation
  const updateLanguageMutation = useMutation({
    mutationFn: ({ code, data }: { code: string; data: { is_enabled?: boolean; is_default?: boolean } }) =>
      apiClient.languageService.updateLanguage(code, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['languages'] })
      queryClient.invalidateQueries({ queryKey: ['language-stats'] })
      toast.success('Language updated')
    },
  })

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: (languageCode: string) => apiClient.languageService.exportTranslations(languageCode),
    onSuccess: (data) => {
      toast.success(data.message)
      // In production, trigger download
      console.log('Export data:', data.data)
    },
  })

  // Auto-translate mutation
  const autoTranslateMutation = useMutation({
    mutationFn: (languageCode: string) => apiClient.languageService.autoTranslate(languageCode),
    onSuccess: (data) => {
      toast.success(data.message)
      if (data.note) toast.info(data.note)
    },
  })

  const filteredLanguages = languages.filter((lang: any) =>
    lang.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lang.native_name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const selectedLang = languages.find((l: any) => l.code === selectedLanguage)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Languages className="h-8 w-8 text-primary" />
            Language Settings
          </h1>
          <p className="text-muted-foreground mt-1">Manage application languages and translations</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline"
            onClick={() => selectedLang && exportMutation.mutate(selectedLang.code)}
            disabled={exportMutation.isPending || !selectedLang}
          >
            <Download className="h-4 w-4 mr-2" />Export
          </Button>
          <Button variant="outline"><Upload className="h-4 w-4 mr-2" />Import</Button>
        </div>
      </div>

      {/* Stats */}
      {stats ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg"><Globe className="h-5 w-5 text-blue-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{stats.total_languages}</div>
                  <div className="text-sm text-muted-foreground">Languages</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg"><Check className="h-5 w-5 text-green-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{stats.enabled_languages}</div>
                  <div className="text-sm text-muted-foreground">Active</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg"><MessageSquare className="h-5 w-5 text-purple-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{stats.total_strings.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">Strings</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-100 rounded-lg"><BookOpen className="h-5 w-5 text-yellow-600" /></div>
                <div>
                  <div className="text-2xl font-bold">{Math.round((stats.translated / stats.total_strings) * 100)}%</div>
                  <div className="text-sm text-muted-foreground">Translated</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Language List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Available Languages</CardTitle>
            <CardDescription>Enable or disable languages for your application</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Search languages..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" />
              </div>
            </div>
            {languagesLoading ? (
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-20" />)}
              </div>
            ) : (
              <ScrollArea className="h-[400px]">
                <div className="space-y-2">
                  {filteredLanguages.map((lang: any) => (
                    <div 
                      key={lang.code} 
                      className={`flex items-center justify-between p-4 rounded-lg border ${selectedLanguage === lang.code ? 'border-primary bg-primary/5' : ''} cursor-pointer hover:bg-muted/50`} 
                      onClick={() => setSelectedLanguage(lang.code)}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{lang.flag}</span>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{lang.name}</span>
                            {lang.is_default && <Badge variant="secondary">Default</Badge>}
                          </div>
                          <span className="text-sm text-muted-foreground">{lang.native_name}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="text-sm font-medium">{lang.progress}%</div>
                          <div className="w-20 h-2 bg-muted rounded-full overflow-hidden">
                            <div className={`h-full ${lang.progress === 100 ? 'bg-green-500' : lang.progress > 70 ? 'bg-blue-500' : 'bg-yellow-500'}`} style={{ width: `${lang.progress}%` }} />
                          </div>
                        </div>
                        <Switch 
                          checked={lang.is_enabled} 
                          onCheckedChange={(checked) => updateLanguageMutation.mutate({ code: lang.code, data: { is_enabled: checked } })}
                          disabled={updateLanguageMutation.isPending}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        {/* Selected Language Details */}
        <Card>
          <CardHeader>
            <CardTitle>Language Details</CardTitle>
            <CardDescription>
              {selectedLang?.name || 'Select a language'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedLang ? (
              <div className="space-y-6">
                <div className="text-center">
                  <span className="text-6xl">{selectedLang.flag}</span>
                  <h3 className="text-xl font-bold mt-2">{selectedLang.name}</h3>
                  <p className="text-muted-foreground">{selectedLang.native_name}</p>
                </div>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Translation Progress</span>
                      <span className="font-medium">{selectedLang.progress}%</span>
                    </div>
                    <div className="h-3 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-primary transition-all" style={{ width: `${selectedLang.progress}%` }} />
                    </div>
                  </div>
                  {stats && (
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="text-muted-foreground">Translated</div>
                        <div className="font-bold">{Math.round(stats.total_strings * selectedLang.progress / 100)}</div>
                      </div>
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="text-muted-foreground">Remaining</div>
                        <div className="font-bold">{Math.round(stats.total_strings * (100 - selectedLang.progress) / 100)}</div>
                      </div>
                    </div>
                  )}
                  <div className="space-y-2">
                    <Button className="w-full" variant="outline"><Settings className="h-4 w-4 mr-2" />Edit Translations</Button>
                    <Button 
                      className="w-full" 
                      variant="outline"
                      onClick={() => autoTranslateMutation.mutate(selectedLang.code)}
                      disabled={autoTranslateMutation.isPending}
                    >
                      <RefreshCw className="h-4 w-4 mr-2" />Auto-Translate
                    </Button>
                    {!selectedLang.is_default && (
                      <Button 
                        className="w-full"
                        onClick={() => updateLanguageMutation.mutate({ code: selectedLang.code, data: { is_default: true } })}
                        disabled={updateLanguageMutation.isPending}
                      >
                        Set as Default
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground">Select a language to view details</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Translation Keys Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Translation Updates</CardTitle>
        </CardHeader>
        <CardContent>
          {translationKeys.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No translation keys found
            </div>
          ) : (
            <div className="space-y-2">
              {translationKeys.map((item: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <code className="text-sm bg-muted px-2 py-1 rounded">{item.key}</code>
                    <div className="text-sm text-muted-foreground mt-1">{item.en}</div>
                  </div>
                  <Badge variant={item.status === 'complete' ? 'default' : 'secondary'}>
                    {item.status === 'complete' ? <Check className="h-3 w-3 mr-1" /> : null}
                    {item.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
