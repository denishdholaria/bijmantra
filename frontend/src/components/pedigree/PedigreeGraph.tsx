import { useEffect, useMemo, useState } from 'react'
import CytoscapeComponent from 'react-cytoscapejs'
import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'
import { PedigreeNode } from '@/lib/api-client'

cytoscape.use(dagre)

interface PedigreeGraphProps {
  data: PedigreeNode | null
  onNodeClick?: (nodeId: string) => void
  direction?: 'TB' | 'LR'
}

interface CytoscapeElement {
  data: {
    id: string
    label?: string
    source?: string
    target?: string
    [key: string]: any
  }
}

const transformToElements = (root: PedigreeNode | null): CytoscapeElement[] => {
  if (!root) return []

  const elements: CytoscapeElement[] = []
  const visited = new Set<string>()

  const traverse = (node: PedigreeNode) => {
    if (visited.has(node.id)) return
    visited.add(node.id)

    // Add node
    elements.push({
      data: {
        id: node.id,
        label: node.name || node.id,
        generation: node.generation,
      },
    })

    // Add edges and traverse parents
    // In pedigree, arrows usually point from parent to child.
    // So source is sire/dam, target is current node.
    if (node.sire) {
      elements.push({
        data: {
          id: `${node.sire.id}->${node.id}`,
          source: node.sire.id,
          target: node.id,
        },
      })
      traverse(node.sire)
    }

    if (node.dam) {
      elements.push({
        data: {
          id: `${node.dam.id}->${node.id}`,
          source: node.dam.id,
          target: node.id,
        },
      })
      traverse(node.dam)
    }
  }

  traverse(root)
  return elements
}

const STYLESHEET: any[] = [
  {
    selector: 'node',
    style: {
      'background-color': '#10b981', // Emerald-500
      'label': 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'color': '#ffffff',
      'text-outline-width': 2,
      'text-outline-color': '#059669', // Emerald-600
      'font-size': '10px',
      'width': 40,
      'height': 40,
    },
  },
  {
    selector: 'edge',
    style: {
      'width': 2,
      'line-color': '#94a3b8', // Slate-400
      'target-arrow-color': '#94a3b8',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
    },
  },
  {
    selector: ':selected',
    style: {
      'background-color': '#3b82f6', // Blue-500
      'line-color': '#3b82f6',
      'target-arrow-color': '#3b82f6',
      'source-arrow-color': '#3b82f6',
    },
  },
]

export function PedigreeGraph({ data, onNodeClick, direction = 'TB' }: PedigreeGraphProps) {
  const elements = useMemo(() => transformToElements(data), [data])
  const [cyInstance, setCyInstance] = useState<any>(null)

  useEffect(() => {
    if (!cyInstance) return

    const handleTap = (event: any) => {
      const nodeId = event.target.id()
      onNodeClick?.(nodeId)
    }

    cyInstance.on('tap', 'node', handleTap)
    return () => {
      cyInstance.off('tap', 'node', handleTap)
    }
  }, [cyInstance, onNodeClick])

  return (
    <div className="h-[600px] w-full border rounded-lg overflow-hidden bg-background">
      <CytoscapeComponent
        elements={elements}
        style={{ width: '100%', height: '100%' }}
        stylesheet={STYLESHEET}
        layout={{
          name: 'dagre',
          rankDir: direction,
          spacingFactor: 1.2,
          animate: true,
          animationDuration: 500,
        }}
        cy={(cy: any) => {
          setCyInstance(cy)
          cy.fit(undefined, 50)
        }}
      />
    </div>
  )
}
