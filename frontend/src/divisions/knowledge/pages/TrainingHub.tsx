/**
 * Training Hub
 * 
 * Courses, certifications, and learning paths for plant breeding professionals.
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import {
  Award,
  BookOpen,
  CheckCircle,
  Clock,
  GraduationCap,
  Play,
  Search,
  Star,
  Trophy,
  Users,
} from 'lucide-react';

interface Course {
  id: string;
  title: string;
  description: string;
  category: string;
  level: 'beginner' | 'intermediate' | 'advanced';
  duration: string;
  lessons: number;
  enrolled: number;
  rating: number;
  progress?: number;
  instructor: string;
  tags: string[];
}

interface Certification {
  id: string;
  title: string;
  description: string;
  requirements: string[];
  validityYears: number;
  examDuration: string;
  passingScore: number;
  status?: 'available' | 'in-progress' | 'completed';
}

interface LearningPath {
  id: string;
  title: string;
  description: string;
  courses: string[];
  totalDuration: string;
  certification?: string;
}

// Demo data
const courses: Course[] = [
  {
    id: 'course-1',
    title: 'Introduction to Plant Breeding',
    description: 'Learn the fundamentals of plant breeding, including selection methods, genetic principles, and breeding objectives.',
    category: 'Fundamentals',
    level: 'beginner',
    duration: '8 hours',
    lessons: 12,
    enrolled: 1250,
    rating: 4.8,
    progress: 75,
    instructor: 'Dr. Sarah Chen',
    tags: ['genetics', 'selection', 'basics'],
  },
  {
    id: 'course-2',
    title: 'Marker-Assisted Selection (MAS)',
    description: 'Master the use of molecular markers for efficient selection in breeding programs.',
    category: 'Molecular Breeding',
    level: 'intermediate',
    duration: '12 hours',
    lessons: 18,
    enrolled: 890,
    rating: 4.9,
    instructor: 'Dr. James Wilson',
    tags: ['markers', 'MAS', 'genomics'],
  },
  {
    id: 'course-3',
    title: 'Genomic Selection in Practice',
    description: 'Implement genomic selection strategies using GBLUP and machine learning approaches.',
    category: 'Molecular Breeding',
    level: 'advanced',
    duration: '16 hours',
    lessons: 24,
    enrolled: 456,
    rating: 4.7,
    progress: 30,
    instructor: 'Dr. Maria Santos',
    tags: ['GBLUP', 'genomic selection', 'ML'],
  },
  {
    id: 'course-4',
    title: 'Field Trial Design & Analysis',
    description: 'Design efficient field trials and analyze data using modern statistical methods.',
    category: 'Statistics',
    level: 'intermediate',
    duration: '10 hours',
    lessons: 15,
    enrolled: 780,
    rating: 4.6,
    instructor: 'Dr. Robert Kim',
    tags: ['trials', 'statistics', 'RCBD'],
  },
  {
    id: 'course-5',
    title: 'Seed Production & Quality',
    description: 'Learn seed production techniques, quality testing, and certification processes.',
    category: 'Seed Technology',
    level: 'beginner',
    duration: '6 hours',
    lessons: 10,
    enrolled: 1100,
    rating: 4.5,
    instructor: 'Dr. Emily Brown',
    tags: ['seed', 'quality', 'certification'],
  },
  {
    id: 'course-6',
    title: 'G×E Analysis & Stability',
    description: 'Analyze genotype-by-environment interactions using AMMI and GGE biplot methods.',
    category: 'Statistics',
    level: 'advanced',
    duration: '8 hours',
    lessons: 12,
    enrolled: 320,
    rating: 4.8,
    instructor: 'Dr. Carlos Mendez',
    tags: ['GxE', 'AMMI', 'stability'],
  },
];

const certifications: Certification[] = [
  {
    id: 'cert-1',
    title: 'Certified Plant Breeder (CPB)',
    description: 'Comprehensive certification covering all aspects of modern plant breeding.',
    requirements: [
      'Complete 3 core courses',
      'Pass written examination (80%)',
      'Submit breeding project portfolio',
      '2+ years breeding experience',
    ],
    validityYears: 3,
    examDuration: '3 hours',
    passingScore: 80,
    status: 'in-progress',
  },
  {
    id: 'cert-2',
    title: 'Molecular Breeding Specialist',
    description: 'Advanced certification in molecular breeding techniques and genomic selection.',
    requirements: [
      'Complete MAS and Genomic Selection courses',
      'Pass practical examination',
      'Demonstrate marker analysis proficiency',
    ],
    validityYears: 2,
    examDuration: '2 hours',
    passingScore: 75,
    status: 'available',
  },
  {
    id: 'cert-3',
    title: 'Seed Quality Analyst',
    description: 'Certification for seed testing and quality assurance professionals.',
    requirements: [
      'Complete Seed Production & Quality course',
      'Pass ISTA-aligned examination',
      'Laboratory practical assessment',
    ],
    validityYears: 2,
    examDuration: '2.5 hours',
    passingScore: 70,
    status: 'available',
  },
];

const learningPaths: LearningPath[] = [
  {
    id: 'path-1',
    title: 'Plant Breeder Track',
    description: 'Complete learning path from fundamentals to advanced breeding techniques.',
    courses: ['course-1', 'course-4', 'course-2', 'course-3'],
    totalDuration: '46 hours',
    certification: 'cert-1',
  },
  {
    id: 'path-2',
    title: 'Molecular Breeding Track',
    description: 'Specialized path for molecular breeding and genomics.',
    courses: ['course-2', 'course-3', 'course-6'],
    totalDuration: '36 hours',
    certification: 'cert-2',
  },
  {
    id: 'path-3',
    title: 'Seed Technology Track',
    description: 'Focus on seed production, quality, and certification.',
    courses: ['course-5', 'course-1'],
    totalDuration: '14 hours',
    certification: 'cert-3',
  },
];

export function TrainingHub() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const categories = [...new Set(courses.map(c => c.category))];

  const filteredCourses = courses.filter(course => {
    const matchesSearch = course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCategory = !selectedCategory || course.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const myCourses = courses.filter(c => c.progress !== undefined);

  const getLevelBadge = (level: string) => {
    const colors: Record<string, string> = {
      beginner: 'bg-green-100 text-green-700',
      intermediate: 'bg-yellow-100 text-yellow-700',
      advanced: 'bg-red-100 text-red-700',
    };
    return <Badge className={colors[level]}>{level}</Badge>;
  };

  const getCertStatusBadge = (status?: string) => {
    if (!status) return null;
    const colors: Record<string, string> = {
      available: 'bg-blue-100 text-blue-700',
      'in-progress': 'bg-yellow-100 text-yellow-700',
      completed: 'bg-green-100 text-green-700',
    };
    return <Badge className={colors[status]}>{status.replace('-', ' ')}</Badge>;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <GraduationCap className="h-8 w-8" />
            Training Hub
          </h1>
          <p className="text-muted-foreground mt-1">
            Courses, certifications, and learning paths for plant breeding professionals
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <BookOpen className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{courses.length}</p>
                <p className="text-sm text-muted-foreground">Courses</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Award className="h-8 w-8 text-yellow-500" />
              <div>
                <p className="text-2xl font-bold">{certifications.length}</p>
                <p className="text-sm text-muted-foreground">Certifications</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Trophy className="h-8 w-8 text-purple-500" />
              <div>
                <p className="text-2xl font-bold">{learningPaths.length}</p>
                <p className="text-sm text-muted-foreground">Learning Paths</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-8 w-8 text-green-500" />
              <div>
                <p className="text-2xl font-bold">{myCourses.length}</p>
                <p className="text-sm text-muted-foreground">In Progress</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="courses">
        <TabsList>
          <TabsTrigger value="courses">All Courses</TabsTrigger>
          <TabsTrigger value="my-learning">My Learning</TabsTrigger>
          <TabsTrigger value="certifications">Certifications</TabsTrigger>
          <TabsTrigger value="paths">Learning Paths</TabsTrigger>
        </TabsList>

        <TabsContent value="courses" className="space-y-4 mt-4">
          {/* Search and Filter */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search courses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2 flex-wrap">
              <Button
                variant={selectedCategory === null ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedCategory(null)}
              >
                All
              </Button>
              {categories.map(cat => (
                <Button
                  key={cat}
                  variant={selectedCategory === cat ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedCategory(cat)}
                >
                  {cat}
                </Button>
              ))}
            </div>
          </div>

          {/* Course Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCourses.map(course => (
              <Card key={course.id} className="flex flex-col">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <Badge variant="outline">{course.category}</Badge>
                    {getLevelBadge(course.level)}
                  </div>
                  <CardTitle className="text-lg mt-2">{course.title}</CardTitle>
                  <CardDescription className="line-clamp-2">{course.description}</CardDescription>
                </CardHeader>
                <CardContent className="flex-1">
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      <span>{course.duration}</span>
                      <span>•</span>
                      <span>{course.lessons} lessons</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4" />
                      <span>{course.enrolled.toLocaleString()} enrolled</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                      <span>{course.rating}</span>
                      <span>•</span>
                      <span>{course.instructor}</span>
                    </div>
                  </div>
                  {course.progress !== undefined && (
                    <div className="mt-3">
                      <div className="flex justify-between text-xs mb-1">
                        <span>Progress</span>
                        <span>{course.progress}%</span>
                      </div>
                      <Progress value={course.progress} className="h-2" />
                    </div>
                  )}
                </CardContent>
                <CardFooter>
                  <Button className="w-full">
                    {course.progress !== undefined ? (
                      <>
                        <Play className="h-4 w-4 mr-2" />
                        Continue
                      </>
                    ) : (
                      <>
                        <BookOpen className="h-4 w-4 mr-2" />
                        Enroll
                      </>
                    )}
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="my-learning" className="space-y-4 mt-4">
          {myCourses.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <BookOpen className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium">No courses in progress</h3>
                <p className="text-muted-foreground mt-1">
                  Enroll in a course to start learning
                </p>
                <Button className="mt-4">Browse Courses</Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {myCourses.map(course => (
                <Card key={course.id}>
                  <CardContent className="py-4">
                    <div className="flex items-center gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium">{course.title}</h3>
                          {getLevelBadge(course.level)}
                        </div>
                        <p className="text-sm text-muted-foreground">{course.instructor}</p>
                        <div className="mt-2">
                          <div className="flex justify-between text-xs mb-1">
                            <span>{course.progress}% complete</span>
                            <span>{Math.round((course.lessons * (course.progress || 0)) / 100)} / {course.lessons} lessons</span>
                          </div>
                          <Progress value={course.progress} className="h-2" />
                        </div>
                      </div>
                      <Button>
                        <Play className="h-4 w-4 mr-2" />
                        Continue
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="certifications" className="space-y-4 mt-4">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {certifications.map(cert => (
              <Card key={cert.id} className="flex flex-col">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Award className="h-8 w-8 text-yellow-500" />
                    {getCertStatusBadge(cert.status)}
                  </div>
                  <CardTitle className="text-lg">{cert.title}</CardTitle>
                  <CardDescription>{cert.description}</CardDescription>
                </CardHeader>
                <CardContent className="flex-1">
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm font-medium mb-2">Requirements:</p>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        {cert.requirements.map((req, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <CheckCircle className="h-4 w-4 mt-0.5 text-green-500 shrink-0" />
                            {req}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="flex gap-4 text-sm text-muted-foreground">
                      <span>Valid: {cert.validityYears} years</span>
                      <span>Exam: {cert.examDuration}</span>
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button className="w-full" variant={cert.status === 'in-progress' ? 'default' : 'outline'}>
                    {cert.status === 'in-progress' ? 'Continue Preparation' : 'Start Certification'}
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="paths" className="space-y-4 mt-4">
          <div className="space-y-4">
            {learningPaths.map(path => (
              <Card key={path.id}>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <Trophy className="h-8 w-8 text-purple-500" />
                    <div>
                      <CardTitle>{path.title}</CardTitle>
                      <CardDescription>{path.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>{path.courses.length} courses</span>
                      <span>•</span>
                      <span>{path.totalDuration} total</span>
                      {path.certification && (
                        <>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <Award className="h-4 w-4 text-yellow-500" />
                            Includes certification
                          </span>
                        </>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {path.courses.map(courseId => {
                        const course = courses.find(c => c.id === courseId);
                        return course ? (
                          <Badge key={courseId} variant="outline">
                            {course.title}
                          </Badge>
                        ) : null;
                      })}
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button>Start Learning Path</Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}


export default TrainingHub;
