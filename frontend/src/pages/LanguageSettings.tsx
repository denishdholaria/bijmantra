import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { ScrollArea } from '@/components/ui/scroll-area'
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

interface Language {
  code: string
  name: string
  nativeName: string
  flag: string
  progress: number
  isDefault: boolean
  isEnabled: boolean
}

export function LanguageSettings() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedLanguage, setSelectedLanguage] = useState('en')

  const languages: Language[] = [
    { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸', progress: 100, isDefault: true, isEnabled: true },
    { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸', progress: 95, isDefault: false, isEnabled: true },
    { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷', progress: 88, isDefault: false, isEnabled: true },
    { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇧🇷', progress: 82, isDefault: false, isEnabled: true },
    { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳', progress: 75, isDefault: false, isEnabled: true },
    { code: 'zh', name: 'Chinese', nativeName: '中文', flag: '🇨🇳', progress: 70, isDefault: false, isEnabled: false },
    { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦', progress: 65, isDefault: false, isEnabled: false },
    { code: 'sw', name: 'Swahili', nativeName: 'Kiswahili', flag: '🇰🇪', progress: 45, isDefault: false, isEnabled: false },
    { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵', progress: 40, isDefault: false, isEnabled: false },
    { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪', progress: 35, isDefault: false, isEnabled: false }
  ]

  const translationStats = {
    totalStrings: 2847,
    translated: 2654,
    needsReview: 124,
    untranslated: 69
  }

  const filteredLanguages = languages.filter(lang =>
    lang.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lang.nativeName.toLowerCase().includes(searchQuery.toLowerCase())
  )

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
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
          <Button variant="outline"><Upload className="h-4 w-4 mr-2" />Import</Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><Globe className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{languages.length}</div>
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
                <div className="text-2xl font-bold">{languages.filter(l => l.isEnabled).length}</div>
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
                <div className="text-2xl font-bold">{translationStats.totalStrings.toLocaleString()}</div>
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
                <div className="text-2xl font-bold">{Math.round((translationStats.translated / translationStats.totalStrings) * 100)}%</div>
                <div className="text-sm text-muted-foreground">Translated</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

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
            <ScrollArea className="h-[400px]">
              <div className="space-y-2">
                {filteredLanguages.map((lang) => (
                  <div key={lang.code} className={`flex items-center justify-between p-4 rounded-lg border ${selectedLanguage === lang.code ? 'border-primary bg-primary/5' : ''} cursor-pointer hover:bg-muted/50`} onClick={() => setSelectedLanguage(lang.code)}>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{lang.flag}</span>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{lang.name}</span>
                          {lang.isDefault && <Badge variant="secondary">Default</Badge>}
                        </div>
                        <span className="text-sm text-muted-foreground">{lang.nativeName}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-sm font-medium">{lang.progress}%</div>
                        <div className="w-20 h-2 bg-muted rounded-full overflow-hidden">
                          <div className={`h-full ${lang.progress === 100 ? 'bg-green-500' : lang.progress > 70 ? 'bg-blue-500' : 'bg-yellow-500'}`} style={{ width: `${lang.progress}%` }} />
                        </div>
                      </div>
                      <Switch checked={lang.isEnabled} />
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Selected Language Details */}
        <Card>
          <CardHeader>
            <CardTitle>Language Details</CardTitle>
            <CardDescription>
              {languages.find(l => l.code === selectedLanguage)?.name || 'Select a language'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {(() => {
              const lang = languages.find(l => l.code === selectedLanguage)
              if (!lang) return <p className="text-muted-foreground">Select a language to view details</p>
              return (
                <div className="space-y-6">
                  <div className="text-center">
                    <span className="text-6xl">{lang.flag}</span>
                    <h3 className="text-xl font-bold mt-2">{lang.name}</h3>
                    <p className="text-muted-foreground">{lang.nativeName}</p>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>Translation Progress</span>
                        <span className="font-medium">{lang.progress}%</span>
                      </div>
                      <div className="h-3 bg-muted rounded-full overflow-hidden">
                        <div className="h-full bg-primary transition-all" style={{ width: `${lang.progress}%` }} />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="text-muted-foreground">Translated</div>
                        <div className="font-bold">{Math.round(translationStats.totalStrings * lang.progress / 100)}</div>
                      </div>
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="text-muted-foreground">Remaining</div>
                        <div className="font-bold">{Math.round(translationStats.totalStrings * (100 - lang.progress) / 100)}</div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Button className="w-full" variant="outline"><Settings className="h-4 w-4 mr-2" />Edit Translations</Button>
                      <Button className="w-full" variant="outline"><RefreshCw className="h-4 w-4 mr-2" />Auto-Translate</Button>
                      {!lang.isDefault && <Button className="w-full">Set as Default</Button>}
                    </div>
                  </div>
                </div>
              )
            })()}
          </CardContent>
        </Card>
      </div>

      {/* Translation Keys Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Translation Updates</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[
              { key: 'dashboard.welcome', en: 'Welcome to Bijmantra', es: 'Bienvenido a Bijmantra', status: 'complete' },
              { key: 'trials.create', en: 'Create New Trial', es: 'Crear Nuevo Ensayo', status: 'complete' },
              { key: 'germplasm.search', en: 'Search Germplasm', es: 'Buscar Germoplasma', status: 'complete' },
              { key: 'reports.generate', en: 'Generate Report', es: '', status: 'pending' }
            ].map((item, i) => (
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
        </CardContent>
      </Card>
    </div>
  )
}
