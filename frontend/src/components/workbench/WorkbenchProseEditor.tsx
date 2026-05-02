import { useEffect, useMemo, useRef } from 'react'
import { EditorContent, useEditor } from '@tiptap/react'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import StarterKit from '@tiptap/starter-kit'
import { Bold, Code2, Heading2, Heading3, Italic, List, ListOrdered, Quote } from 'lucide-react'
import { marked } from 'marked'
import TurndownService from 'turndown'
import { gfm } from 'turndown-plugin-gfm'

import { cn } from '@/lib/utils'

import './WorkbenchProseEditor.css'

type WorkbenchProseEditorProps = {
  value: string
  onChange: (value: string) => void
  readOnly?: boolean
  placeholder?: string
  className?: string
}

type ToolbarAction = {
  label: string
  icon: typeof Bold
  isActive: boolean
  onClick: () => void
}

const turndown = new TurndownService({
  bulletListMarker: '-',
  codeBlockStyle: 'fenced',
  headingStyle: 'atx',
})

turndown.use(gfm)

marked.setOptions({
  breaks: true,
  gfm: true,
})

function markdownToHtml(markdown: string) {
  const rendered = marked.parse(markdown)
  return typeof rendered === 'string' ? rendered : ''
}

function htmlToMarkdown(html: string) {
  return turndown.turndown(html).replace(/\n{3,}/g, '\n\n').trimEnd() + '\n'
}

function ToolbarButton({ action, disabled }: { action: ToolbarAction; disabled: boolean }) {
  const Icon = action.icon

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={action.onClick}
      aria-label={action.label}
      className={cn(
        'inline-flex h-9 w-9 items-center justify-center rounded-xl border text-shell transition disabled:cursor-not-allowed disabled:opacity-45',
        action.isActive
          ? 'border-emerald-300/70 bg-emerald-50 text-emerald-700 dark:border-emerald-700/60 dark:bg-emerald-900/35 dark:text-emerald-200'
          : 'border-slate-200/70 bg-white/80 hover:border-emerald-300 hover:text-emerald-700 dark:border-slate-800 dark:bg-slate-950/60 dark:hover:border-emerald-700 dark:hover:text-emerald-200'
      )}
    >
      <Icon className="h-4 w-4" />
    </button>
  )
}

export function WorkbenchProseEditor({
  value,
  onChange,
  readOnly = false,
  placeholder = 'Start writing your report...',
  className,
}: WorkbenchProseEditorProps) {
  const lastExternalValueRef = useRef(value)

  const editor = useEditor({
    immediatelyRender: false,
    editable: !readOnly,
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3],
        },
      }),
      Link.configure({
        autolink: true,
        openOnClick: false,
      }),
      Placeholder.configure({
        placeholder,
      }),
    ],
    content: markdownToHtml(value),
    editorProps: {
      attributes: {
        class:
          'workbench-prose-editor min-h-full bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.96))] px-6 py-5 text-shell dark:bg-[linear-gradient(180deg,rgba(2,6,23,0.94),rgba(3,7,18,0.98))]',
        'data-placeholder': placeholder,
        'data-testid': 'desktop-prose-editor',
        'aria-label': 'Workbench prose editor',
      },
    },
    onUpdate({ editor: nextEditor }) {
      const nextMarkdown = htmlToMarkdown(nextEditor.getHTML())
      lastExternalValueRef.current = nextMarkdown
      onChange(nextMarkdown)
    },
  })

  useEffect(() => {
    if (!editor) {
      return
    }

    editor.setEditable(!readOnly)
  }, [editor, readOnly])

  useEffect(() => {
    if (!editor || value === lastExternalValueRef.current) {
      return
    }

    lastExternalValueRef.current = value
    editor.commands.setContent(markdownToHtml(value), { emitUpdate: false })
  }, [editor, value])

  const toolbarActions = useMemo<ToolbarAction[]>(() => {
    if (!editor) {
      return []
    }

    return [
      {
        label: 'Heading 2',
        icon: Heading2,
        isActive: editor.isActive('heading', { level: 2 }),
        onClick: () => editor.chain().focus().toggleHeading({ level: 2 }).run(),
      },
      {
        label: 'Heading 3',
        icon: Heading3,
        isActive: editor.isActive('heading', { level: 3 }),
        onClick: () => editor.chain().focus().toggleHeading({ level: 3 }).run(),
      },
      {
        label: 'Bold',
        icon: Bold,
        isActive: editor.isActive('bold'),
        onClick: () => editor.chain().focus().toggleBold().run(),
      },
      {
        label: 'Italic',
        icon: Italic,
        isActive: editor.isActive('italic'),
        onClick: () => editor.chain().focus().toggleItalic().run(),
      },
      {
        label: 'Bullet list',
        icon: List,
        isActive: editor.isActive('bulletList'),
        onClick: () => editor.chain().focus().toggleBulletList().run(),
      },
      {
        label: 'Ordered list',
        icon: ListOrdered,
        isActive: editor.isActive('orderedList'),
        onClick: () => editor.chain().focus().toggleOrderedList().run(),
      },
      {
        label: 'Quote',
        icon: Quote,
        isActive: editor.isActive('blockquote'),
        onClick: () => editor.chain().focus().toggleBlockquote().run(),
      },
      {
        label: 'Code block',
        icon: Code2,
        isActive: editor.isActive('codeBlock'),
        onClick: () => editor.chain().focus().toggleCodeBlock().run(),
      },
    ]
  }, [editor])

  return (
    <div className={cn('flex h-full min-h-[24rem] flex-col overflow-hidden', className)}>
      <div className="border-shell flex flex-wrap items-center gap-2 border-b bg-[hsl(var(--app-shell-panel)/0.74)] px-4 py-3">
        {toolbarActions.map((action) => (
          <ToolbarButton key={action.label} action={action} disabled={readOnly || !editor} />
        ))}
        <span className="ml-auto text-[11px] uppercase tracking-[0.22em] text-shell-muted">
          {readOnly ? 'Read only prose surface' : 'Markdown-backed writing surface'}
        </span>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        <EditorContent editor={editor} className="h-full" />
      </div>
    </div>
  )
}