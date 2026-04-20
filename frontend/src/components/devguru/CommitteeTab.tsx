import { CommitteeMember, Meeting, FeedbackItem, CollaborationStats } from '@/types/devguru'
import { cn } from '@/lib/utils'

interface CommitteeTabProps {
  members: CommitteeMember[]
  meetings: Meeting[]
  feedback: FeedbackItem[]
  stats: CollaborationStats | undefined
  isLoading: boolean
}

export function CommitteeTab({ members, meetings, stats, isLoading }: CommitteeTabProps) {
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
          <p className="text-sm text-gray-500">Loading committee data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-purple-600">{stats.committee_size}</p>
            <p className="text-xs text-purple-700">Members</p>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-blue-600">{stats.upcoming_meetings}</p>
            <p className="text-xs text-blue-700">Upcoming</p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-green-600">{stats.completed_meetings}</p>
            <p className="text-xs text-green-700">Completed</p>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-yellow-600">{stats.pending_feedback}</p>
            <p className="text-xs text-yellow-700">Pending</p>
          </div>
        </div>
      )}

      {/* Members */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Committee Members</h4>
        {members.length === 0 ? (
          <p className="text-sm text-gray-500">No committee members yet.</p>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {members.map(member => (
              <div key={member.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                <p className="font-medium text-gray-900 dark:text-white">{member.name}</p>
                <p className="text-xs text-gray-500">{member.role}</p>
                {member.institution && <p className="text-xs text-gray-400">{member.institution}</p>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Meetings */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Meetings</h4>
        {meetings.length === 0 ? (
          <p className="text-sm text-gray-500">No meetings scheduled.</p>
        ) : (
          <div className="space-y-2">
            {meetings.slice(0, 5).map(meeting => (
              <div key={meeting.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                <div className="flex justify-between">
                  <p className="font-medium text-gray-900 dark:text-white">{meeting.title}</p>
                  <span className={cn(
                    'text-xs px-2 py-1 rounded',
                    meeting.status === 'completed' ? 'bg-green-100 text-green-700' :
                    meeting.status === 'scheduled' ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-700'
                  )}>
                    {meeting.status}
                  </span>
                </div>
                <p className="text-xs text-gray-500">{new Date(meeting.scheduled_date).toLocaleDateString()}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
