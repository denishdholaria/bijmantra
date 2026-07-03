import { fireEvent, render, screen } from '@testing-library/react'
import type { ComponentProps } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { ReevuComposer } from './ReevuComposer'
import type { ReevuAttachment } from '@/hooks/useReevuChat'

const baseVoice = {
	isListening: false,
	startListening: vi.fn(),
	stopListening: vi.fn(),
	isSupported: true,
	error: null,
}

const attachment: ReevuAttachment = {
	id: 'file-1',
	name: 'trial-summary.csv',
	size: 2048,
	mime_type: 'text/csv',
	status: 'ready',
	preview: 'plot,yield\nA,42',
}

function renderComposer(overrides: Partial<ComponentProps<typeof ReevuComposer>> = {}) {
	const props: ComponentProps<typeof ReevuComposer> = {
		input: '',
		setInput: vi.fn(),
		isProcessing: false,
		onSend: vi.fn(),
		voice: baseVoice,
		agentMode: 'auto',
		onAgentModeChange: vi.fn(),
		attachments: [],
		onAttachFiles: vi.fn(),
		onRemoveAttachment: vi.fn(),
		...overrides,
	}

	return {
		props,
		...render(<ReevuComposer {...props} />),
	}
}

describe('ReevuComposer', () => {
	it('allows selecting an agent mode', () => {
		const onAgentModeChange = vi.fn()
		renderComposer({ onAgentModeChange })

		fireEvent.click(screen.getByRole('button', { name: /validate/i }))

		expect(onAgentModeChange).toHaveBeenCalledWith('validate')
	})

	it('renders attachment chips and removes an attachment', () => {
		const onRemoveAttachment = vi.fn()
		renderComposer({ attachments: [attachment], onRemoveAttachment })

		expect(screen.getByText('trial-summary.csv')).toBeInTheDocument()

		fireEvent.click(screen.getByRole('button', { name: /remove trial-summary\.csv/i }))

		expect(onRemoveAttachment).toHaveBeenCalledWith('file-1')
	})

	it('can send with an attachment-only prompt', () => {
		const onSend = vi.fn()
		renderComposer({ attachments: [attachment], onSend })

		fireEvent.click(screen.getByRole('button', { name: /send message to reevu/i }))

		expect(onSend).toHaveBeenCalled()
	})

	it('passes selected files to the attachment handler', () => {
		const onAttachFiles = vi.fn()
		renderComposer({ onAttachFiles })

		const file = new File(['plot,yield\nA,42'], 'plot.csv', { type: 'text/csv' })
		fireEvent.change(screen.getByLabelText(/attach files to reevu/i), {
			target: { files: [file] },
		})

		expect(onAttachFiles).toHaveBeenCalled()
	})
})
