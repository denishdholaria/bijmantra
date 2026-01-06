import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  GraduationCap, Play, CheckCircle, Clock, Award,
  BookOpen, Video, FileText, Users, Star, Lock
} from 'lucide-react'

interface Course {
  id: string
  title: string
  description: string
  category: string
  duration: string
  lessons: number
  completedLessons: number
  level: 'beginner' | 'intermediate' | 'advanced'
  instructor: string
  rating: number
  enrolled: boolean
}

interface Certificate {
  id: string
  name: string
  issuedDate: string
  course: string
}

export function TrainingHub() {
  const [activeTab, setActiveTab] = useState('courses')
  const [selectedCategory, setSelectedCategory] = useState('all')

  const courses: Course[] = [
    { id: '1', title: 'Introduction to Plant Breeding', description: 'Fundamentals of plant breeding and genetics', category: 'breeding', duration: '4 hours', lessons: 12, completedLessons: 12, level: 'beginner', instructor: 'Dr. Sarah Chen', rating: 4.8, enrolled: true },
    { id: '2', title: 'Genomic Selection in Practice', description: 'Implementing GS in breeding programs', category: 'genomics', duration: '6 hours', lessons: 18, completedLessons: 10, level: 'advanced', instructor: 'Raj Patel', rating: 4.9, enrolled: true },
    { id: '3', title: 'Field Trial Design', description: 'Statistical designs for field experiments', category: 'statistics', duration: '3 hours', lessons: 8, completedLessons: 0, level: 'intermediate', instructor: 'John Smith', rating: 4.7, enrolled: false },
    { id: '4', title: 'Phenotyping Best Practices', description: 'Data collection and quality control', category: 'phenotyping', duration: '2 hours', lessons: 6, completedLessons: 6, level: 'beginner', instructor: 'Maria Garcia', rating: 4.6, enrolled: true },
    { id: '5', title: 'Molecular Markers in Breeding', description: 'MAS and marker development', category: 'genomics', duration: '5 hours', lessons: 15, completedLessons: 0, level: 'intermediate', instructor: 'Aisha Okonkwo', rating: 4.8, enrolled: false },
    { id: '6', title: 'BrAPI Data Management', description: 'Using BrAPI for data interoperability', category: 'data', duration: '3 hours', lessons: 9, completedLessons: 5, level: 'intermediate', instructor: 'Chen Wei', rating: 4.5, enrolled: true },
  ]

  const certificates: Certificate[] = [
    { id: '1', name: 'Plant Breeding Fundamentals', issuedDate: '2025-10-15', course: 'Introduction to Plant Breeding' },
    { id: '2', name: 'Phenotyping Specialist', issuedDate: '2025-11-20', course: 'Phenotyping Best Practices' },
  ]

  const categories = [
    { value: 'all', label: 'All Courses' },
    { value: 'breeding', label: 'Breeding' },
    { value: 'genomics', label: 'Genomics' },
    { value: 'statistics', label: 'Statistics' },
    { value: 'phenotyping', label: 'Phenotyping' },
    { value: 'data', label: 'Data Management' },
  ]

  const enrolledCourses = courses.filter(c => c.enrolled)
  const completedCourses = enrolledCourses.filter(c => c.completedLessons === c.lessons)
  const inProgressCourses = enrolledCourses.filter(c => c.completedLessons > 0 && c.completedLessons < c.lessons)

  const getLevelColor = (level: string) => {
    const colors: Record<string, string> = { beginner: 'bg-green-100 text-green-800', intermediate: 'bg-yellow-100 text-yellow-800', advanced: 'bg-red-100 text-red-800' }
    return colors[level] || 'bg-gray-100 text-gray-800'
  }

  const filteredCourses = courses.filter(c => selectedCategory === 'all' || c.category === selectedCategory)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Training Hub</h1>
          <p className="text-muted-foreground">Learn plant breeding skills and earn certificates</p>
        </div>
        <Button><GraduationCap className="mr-2 h-4 w-4" />My Learning</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Enrolled</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{enrolledCourses.length}</div>
            <p className="text-xs text-muted-foreground">Active courses</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{inProgressCourses.length}</div>
            <p className="text-xs text-muted-foreground">Continue learning</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completedCourses.length}</div>
            <p className="text-xs text-muted-foreground">Finished courses</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Certificates</CardTitle>
            <Award className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{certificates.length}</div>
            <p className="text-xs text-muted-foreground">Earned</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="courses"><BookOpen className="mr-2 h-4 w-4" />All Courses</TabsTrigger>
          <TabsTrigger value="my-learning"><Play className="mr-2 h-4 w-4" />My Learning</TabsTrigger>
          <TabsTrigger value="certificates"><Award className="mr-2 h-4 w-4" />Certificates</TabsTrigger>
        </TabsList>

        <TabsContent value="courses" className="space-y-4">
          <div className="flex gap-2 flex-wrap">
            {categories.map(cat => (
              <Button key={cat.value} variant={selectedCategory === cat.value ? 'default' : 'outline'} size="sm" onClick={() => setSelectedCategory(cat.value)}>{cat.label}</Button>
            ))}
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredCourses.map((course) => (
              <Card key={course.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{course.title}</CardTitle>
                      <CardDescription>{course.description}</CardDescription>
                    </div>
                    <Badge className={getLevelColor(course.level)}>{course.level}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1"><Video className="h-3 w-3" />{course.lessons} lessons</span>
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{course.duration}</span>
                      <span className="flex items-center gap-1"><Star className="h-3 w-3 text-yellow-500" />{course.rating}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">By {course.instructor}</p>
                    {course.enrolled ? (
                      <div className="space-y-2">
                        <Progress value={(course.completedLessons / course.lessons) * 100} />
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-muted-foreground">{course.completedLessons}/{course.lessons} completed</span>
                          <Button size="sm">{course.completedLessons === course.lessons ? 'Review' : 'Continue'}</Button>
                        </div>
                      </div>
                    ) : (
                      <Button className="w-full">Enroll Now</Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="my-learning" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {enrolledCourses.filter(c => c.completedLessons < c.lessons).map((course) => (
              <Card key={course.id}>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-4">
                    <div className="h-16 w-16 rounded-lg bg-primary/10 flex items-center justify-center"><GraduationCap className="h-8 w-8 text-primary" /></div>
                    <div className="flex-1">
                      <p className="font-medium">{course.title}</p>
                      <Progress value={(course.completedLessons / course.lessons) * 100} className="mt-2" />
                      <p className="text-xs text-muted-foreground mt-1">{course.completedLessons}/{course.lessons} lessons</p>
                    </div>
                    <Button><Play className="mr-2 h-4 w-4" />Resume</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="certificates" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {certificates.map((cert) => (
              <Card key={cert.id} className="border-2 border-primary/20">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-4">
                    <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center"><Award className="h-8 w-8 text-primary" /></div>
                    <div className="flex-1">
                      <p className="font-medium">{cert.name}</p>
                      <p className="text-sm text-muted-foreground">{cert.course}</p>
                      <p className="text-xs text-muted-foreground">Issued: {cert.issuedDate}</p>
                    </div>
                    <Button variant="outline">Download</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
