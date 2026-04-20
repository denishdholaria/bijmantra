import { useState } from 'react'
import { addPaper } from '@/services/devguru'

interface AddPaperModalProps {
  projectId: string
  onClose: () => void
  onAdded: () => void
}

export function AddPaperModal({ projectId, onClose, onAdded }: AddPaperModalProps) {
  const [formData, setFormData] = useState({
    title: '',
    authors: '',
    journal: '',
    year: '',
    doi: '',
    notes: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title) return
    setIsSubmitting(true)
    try {
      await addPaper(projectId, {
        title: formData.title,
        authors: formData.authors.split(',').map((a: string) => a.trim()).filter(Boolean),
        journal: formData.journal || undefined,
        year: formData.year ? parseInt(formData.year) : undefined,
        doi: formData.doi || undefined,
        notes: formData.notes || undefined,
        tags: [],
        read_status: 'unread'
      })
      onAdded()
    } catch (error) {
      console.error('Failed to add paper:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md mx-4">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">📚 Add Paper</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Title *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Authors (comma-separated)</label>
            <input
              type="text"
              value={formData.authors}
              onChange={(e) => setFormData(prev => ({ ...prev, authors: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Smith J, Doe A"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Journal</label>
              <input
                type="text"
                value={formData.journal}
                onChange={(e) => setFormData(prev => ({ ...prev, journal: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Year</label>
              <input
                type="number"
                value={formData.year}
                onChange={(e) => setFormData(prev => ({ ...prev, year: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
            <button
              type="submit"
              disabled={isSubmitting || !formData.title}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Adding...' : 'Add Paper'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
