import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { cn } from '@/lib/utils'

type WorkbenchMarkdownPreviewProps = {
  value: string
  className?: string
}

export function WorkbenchMarkdownPreview({ value, className }: WorkbenchMarkdownPreviewProps) {
  return (
    <div
      className={cn(
        'text-[13px] leading-6 text-slate-200 [&_a]:text-emerald-300 [&_a]:underline [&_blockquote]:border-l-2 [&_blockquote]:border-white/15 [&_blockquote]:pl-3 [&_blockquote]:text-slate-400 [&_code]:rounded [&_code]:bg-white/8 [&_code]:px-1.5 [&_code]:py-0.5 [&_h1]:mt-5 [&_h1]:text-2xl [&_h1]:font-semibold [&_h2]:mt-4 [&_h2]:text-xl [&_h2]:font-semibold [&_h3]:mt-3 [&_h3]:text-lg [&_h3]:font-semibold [&_li]:ml-5 [&_li]:list-disc [&_ol]:space-y-1 [&_p]:mb-3 [&_pre]:overflow-x-auto [&_pre]:rounded-2xl [&_pre]:bg-black/30 [&_pre]:p-4 [&_pre]:text-[12px] [&_table]:w-full [&_table]:border-collapse [&_tbody_tr]:border-b [&_tbody_tr]:border-white/8 [&_td]:border [&_td]:border-white/8 [&_td]:px-3 [&_td]:py-2 [&_th]:border [&_th]:border-white/8 [&_th]:bg-white/5 [&_th]:px-3 [&_th]:py-2 [&_th]:text-left [&_ul]:space-y-1',
        className
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{value}</ReactMarkdown>
    </div>
  )
}