import { Routes, Route, NavLink } from 'react-router-dom'
import PapersPage from './pages/PapersPage'
import PaperDetailPage from './pages/PaperDetailPage'
import GraphPage from './pages/GraphPage'
import styles from './App.module.css'

export default function App() {
  return (
    <div className={styles.layout}>
      <nav className={styles.nav}>
        <span className={styles.logo}>Paper Archive</span>
        <NavLink to="/" end className={({ isActive }) => isActive ? styles.active : ''}>Papers</NavLink>
        <NavLink to="/graph" className={({ isActive }) => isActive ? styles.active : ''}>Graph</NavLink>
      </nav>
      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<PapersPage />} />
          <Route path="/papers/:id" element={<PaperDetailPage />} />
          <Route path="/graph" element={<GraphPage />} />
        </Routes>
      </main>
    </div>
  )
}
