import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-primary-600 text-white shadow-lg">
          <div className="container mx-auto px-4 py-6">
            <h1 className="text-3xl font-bold">🌱 Bijmantra</h1>
            <p className="text-primary-100 mt-1">Plant Breeding Application</p>
          </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<HomePage />} />
            {/* Add more routes here */}
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-gray-800 text-gray-300 mt-12">
          <div className="container mx-auto px-4 py-6 text-center">
            <p>© 2025 Bijmantra - BrAPI v2.1 Compliant</p>
          </div>
        </footer>
      </div>
    </Router>
  )
}

// Home Page Component
function HomePage() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          Welcome to Bijmantra
        </h2>
        <p className="text-gray-600 mb-6">
          A modern, offline-capable plant breeding application built with BrAPI v2.1 specification.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Feature Cards */}
          <FeatureCard
            icon="🌾"
            title="Programs & Trials"
            description="Manage breeding programs, trials, and studies"
          />
          <FeatureCard
            icon="📊"
            title="Phenotyping"
            description="Collect and analyze phenotypic observations"
          />
          <FeatureCard
            icon="🧬"
            title="Genotyping"
            description="Manage genotyping data and variants"
          />
          <FeatureCard
            icon="🌱"
            title="Germplasm"
            description="Track germplasm, pedigrees, and crosses"
          />
        </div>

        <div className="mt-8 p-4 bg-primary-50 rounded-lg border border-primary-200">
          <h3 className="font-semibold text-primary-800 mb-2">
            🚀 Getting Started
          </h3>
          <p className="text-primary-700 text-sm">
            This is a Progressive Web App (PWA). You can install it on your device for offline access.
            Perfect for field data collection!
          </p>
        </div>
      </div>
    </div>
  )
}

// Feature Card Component
function FeatureCard({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="p-6 bg-gray-50 rounded-lg border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-800 mb-2">{title}</h3>
      <p className="text-gray-600 text-sm">{description}</p>
    </div>
  )
}

export default App
