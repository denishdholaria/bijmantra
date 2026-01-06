/**
 * Person Form - Create/Edit person
 * BrAPI v2.1 Core Module
 */

import { useForm } from 'react-hook-form'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, Link, useParams } from 'react-router-dom'
import { useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from 'sonner'

interface PersonFormData {
  firstName: string
  lastName: string
  middleName: string
  emailAddress: string
  phoneNumber: string
  userType: string
  description: string
  mailingAddress: string
  instituteName: string
  orcid: string
}

export function PersonForm() {
  const { id } = useParams<{ id: string }>()
  const isEdit = !!id
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { register, handleSubmit, setValue, watch, reset, formState: { errors } } = useForm<PersonFormData>()

  const { data: existingData } = useQuery({
    queryKey: ['person', id],
    queryFn: () => apiClient.getPerson(id!),
    enabled: isEdit,
  })

  useEffect(() => {
    if (existingData?.result) {
      const p = existingData.result
      reset({
        firstName: p.firstName || '',
        lastName: p.lastName || '',
        middleName: p.middleName || '',
        emailAddress: p.emailAddress || '',
        phoneNumber: p.phoneNumber || '',
        userType: p.userType || '',
        description: p.description || '',
        mailingAddress: p.mailingAddress || '',
        instituteName: p.instituteName || '',
        orcid: p.orcid || '',
      })
    }
  }, [existingData, reset])

  const mutation = useMutation({
    mutationFn: (data: PersonFormData) => {
      const payload = {
        firstName: data.firstName,
        lastName: data.lastName,
        middleName: data.middleName || undefined,
        emailAddress: data.emailAddress || undefined,
        phoneNumber: data.phoneNumber || undefined,
        userType: data.userType || undefined,
        description: data.description || undefined,
        mailingAddress: data.mailingAddress || undefined,
        instituteName: data.instituteName || undefined,
        orcid: data.orcid || undefined,
      }
      return isEdit 
        ? apiClient.updatePerson(id!, payload)
        : apiClient.createPerson(payload)
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      toast.success(isEdit ? 'Person updated!' : 'Person added!')
      const personId = response.result?.personDbId || id
      navigate(personId ? `/people/${personId}` : '/people')
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to save person')
    },
  })

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild><Link to="/people">←</Link></Button>
            <div>
              <CardTitle>{isEdit ? 'Edit Person' : 'Add Person'}</CardTitle>
              <CardDescription>Team member or contact (BrAPI v2.1)</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="firstName">First Name *</Label>
                <Input id="firstName" {...register('firstName', { required: 'Required' })} placeholder="John" />
                {errors.firstName && <p className="text-sm text-red-600">{errors.firstName.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="middleName">Middle Name</Label>
                <Input id="middleName" {...register('middleName')} placeholder="M." />
              </div>
              <div className="space-y-2">
                <Label htmlFor="lastName">Last Name *</Label>
                <Input id="lastName" {...register('lastName', { required: 'Required' })} placeholder="Doe" />
                {errors.lastName && <p className="text-sm text-red-600">{errors.lastName.message}</p>}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="emailAddress">Email</Label>
                <Input id="emailAddress" type="email" {...register('emailAddress')} placeholder="john.doe@example.org" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phoneNumber">Phone</Label>
                <Input id="phoneNumber" {...register('phoneNumber')} placeholder="+1 234 567 8900" />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Role/Type</Label>
                <Select value={watch('userType')} onValueChange={(v) => setValue('userType', v)}>
                  <SelectTrigger><SelectValue placeholder="Select role..." /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Researcher">Researcher</SelectItem>
                    <SelectItem value="Technician">Technician</SelectItem>
                    <SelectItem value="Breeder">Breeder</SelectItem>
                    <SelectItem value="Data Manager">Data Manager</SelectItem>
                    <SelectItem value="Administrator">Administrator</SelectItem>
                    <SelectItem value="Student">Student</SelectItem>
                    <SelectItem value="External">External Contact</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="instituteName">Institution</Label>
                <Input id="instituteName" {...register('instituteName')} placeholder="University of..." />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="mailingAddress">Address</Label>
              <Textarea id="mailingAddress" {...register('mailingAddress')} rows={2} placeholder="Street, City, Country" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="orcid">ORCID</Label>
                <Input id="orcid" {...register('orcid')} placeholder="0000-0000-0000-0000" />
                <p className="text-xs text-muted-foreground">Researcher identifier from orcid.org</p>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Notes</Label>
              <Textarea id="description" {...register('description')} rows={2} placeholder="Additional notes..." />
            </div>

            <div className="flex gap-3 pt-4 border-t">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? '👤 Saving...' : isEdit ? '👤 Update Person' : '👤 Add Person'}
              </Button>
              <Button variant="outline" asChild><Link to="/people">Cancel</Link></Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
