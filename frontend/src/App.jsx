import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { BookmarkIcon, MessageCircleIcon, ThumbsUpIcon, ThumbsDownIcon, SearchIcon, PlusIcon, UserIcon } from 'lucide-react'
import './App.css'

const API_BASE_URL = 'http://localhost:5001/api'

function App() {
  const [user, setUser] = useState(null)
  const [papers, setPapers] = useState([])
  const [bookmarks, setBookmarks] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState('home')

  useEffect(() => {
    // Check if user is logged in (simple localStorage check)
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    }
    
    // Load papers
    fetchPapers()
  }, [])

  useEffect(() => {
    if (user) {
      fetchBookmarks()
    }
  }, [user])

  const fetchPapers = async (search = '') => {
    try {
      const response = await fetch(`${API_BASE_URL}/papers?search=${search}`)
      const data = await response.json()
      setPapers(data.papers || [])
    } catch (error) {
      console.error('Error fetching papers:', error)
    }
  }

  const fetchBookmarks = async () => {
    if (!user) return
    try {
      const response = await fetch(`${API_BASE_URL}/users/${user.id}/bookmarks`)
      const data = await response.json()
      setBookmarks(data || [])
    } catch (error) {
      console.error('Error fetching bookmarks:', error)
    }
  }

  const handleLogin = async (username, password) => {
    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      const data = await response.json()
      if (response.ok) {
        setUser(data.user)
        localStorage.setItem('user', JSON.stringify(data.user))
        return true
      } else {
        alert(data.error)
        return false
      }
    } catch (error) {
      console.error('Login error:', error)
      return false
    }
  }

  const handleRegister = async (username, email, password, affiliation, fieldOfStudy) => {
    try {
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          username, 
          email, 
          password, 
          affiliation, 
          field_of_study: fieldOfStudy 
        })
      })
      const data = await response.json()
      if (response.ok) {
        setUser(data.user)
        localStorage.setItem('user', JSON.stringify(data.user))
        return true
      } else {
        alert(data.error)
        return false
      }
    } catch (error) {
      console.error('Register error:', error)
      return false
    }
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('user')
    setCurrentPage('home')
  }

  const handleSearch = () => {
    fetchPapers(searchQuery)
  }

  const addPaper = async (doi, arxivId) => {
    if (!user) {
      alert('ログインが必要です')
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/papers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          user_id: user.id,
          doi: doi || undefined,
          arxiv_id: arxivId || undefined
        })
      })
      const data = await response.json()
      if (response.ok) {
        fetchPapers()
        alert('論文が追加されました')
        return true
      } else {
        alert(data.error)
        return false
      }
    } catch (error) {
      console.error('Add paper error:', error)
      return false
    }
  }

  const toggleBookmark = async (paperId) => {
    if (!user) {
      alert('ログインが必要です')
      return
    }

    const isBookmarked = bookmarks.some(b => b.paper_id === paperId)
    
    try {
      if (isBookmarked) {
        const response = await fetch(`${API_BASE_URL}/users/${user.id}/bookmarks/${paperId}`, {
          method: 'DELETE'
        })
        if (response.ok) {
          fetchBookmarks()
        }
      } else {
        const response = await fetch(`${API_BASE_URL}/users/${user.id}/bookmarks`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ paper_id: paperId })
        })
        if (response.ok) {
          fetchBookmarks()
        }
      }
    } catch (error) {
      console.error('Bookmark error:', error)
    }
  }

  if (!user) {
    return <AuthPage onLogin={handleLogin} onRegister={handleRegister} />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header user={user} onLogout={handleLogout} currentPage={currentPage} setCurrentPage={setCurrentPage} />
      
      <main className="container mx-auto px-4 py-8">
        {currentPage === 'home' && (
          <HomePage 
            papers={papers}
            bookmarks={bookmarks}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            onSearch={handleSearch}
            onToggleBookmark={toggleBookmark}
            onAddPaper={addPaper}
          />
        )}
        
        {currentPage === 'bookmarks' && (
          <BookmarksPage bookmarks={bookmarks} onToggleBookmark={toggleBookmark} />
        )}
      </main>
    </div>
  )
}

function Header({ user, onLogout, currentPage, setCurrentPage }) {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-blue-600 cursor-pointer" onClick={() => setCurrentPage('home')}>
          PaperWeaver
        </h1>
        
        <nav className="flex items-center space-x-4">
          <Button 
            variant={currentPage === 'home' ? 'default' : 'ghost'}
            onClick={() => setCurrentPage('home')}
          >
            ホーム
          </Button>
          <Button 
            variant={currentPage === 'bookmarks' ? 'default' : 'ghost'}
            onClick={() => setCurrentPage('bookmarks')}
          >
            ブックマーク
          </Button>
          
          <div className="flex items-center space-x-2">
            <UserIcon className="h-4 w-4" />
            <span className="text-sm">{user.username}</span>
            <Button variant="outline" size="sm" onClick={onLogout}>
              ログアウト
            </Button>
          </div>
        </nav>
      </div>
    </header>
  )
}

function AuthPage({ onLogin, onRegister }) {
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    affiliation: '',
    fieldOfStudy: ''
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (isLogin) {
      await onLogin(formData.username, formData.password)
    } else {
      await onRegister(
        formData.username, 
        formData.email, 
        formData.password, 
        formData.affiliation, 
        formData.fieldOfStudy
      )
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center text-2xl text-blue-600">PaperWeaver</CardTitle>
          <CardDescription className="text-center">
            学術文献探索・議論プラットフォーム
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={isLogin ? 'login' : 'register'} onValueChange={(value) => setIsLogin(value === 'login')}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">ログイン</TabsTrigger>
              <TabsTrigger value="register">新規登録</TabsTrigger>
            </TabsList>
            
            <TabsContent value="login">
              <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                  placeholder="ユーザー名"
                  value={formData.username}
                  onChange={(e) => setFormData({...formData, username: e.target.value})}
                  required
                />
                <Input
                  type="password"
                  placeholder="パスワード"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                />
                <Button type="submit" className="w-full">ログイン</Button>
              </form>
            </TabsContent>
            
            <TabsContent value="register">
              <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                  placeholder="ユーザー名"
                  value={formData.username}
                  onChange={(e) => setFormData({...formData, username: e.target.value})}
                  required
                />
                <Input
                  type="email"
                  placeholder="メールアドレス"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                />
                <Input
                  type="password"
                  placeholder="パスワード"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                />
                <Input
                  placeholder="所属（任意）"
                  value={formData.affiliation}
                  onChange={(e) => setFormData({...formData, affiliation: e.target.value})}
                />
                <Input
                  placeholder="専門分野（任意）"
                  value={formData.fieldOfStudy}
                  onChange={(e) => setFormData({...formData, fieldOfStudy: e.target.value})}
                />
                <Button type="submit" className="w-full">新規登録</Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}

function HomePage({ papers, bookmarks, searchQuery, setSearchQuery, onSearch, onToggleBookmark, onAddPaper }) {
  const [showAddPaper, setShowAddPaper] = useState(false)
  const [paperForm, setPaperForm] = useState({ doi: '', arxivId: '' })

  const handleAddPaper = async (e) => {
    e.preventDefault()
    if (!paperForm.doi && !paperForm.arxivId) {
      alert('DOIまたはarXiv IDを入力してください')
      return
    }
    
    const success = await onAddPaper(paperForm.doi, paperForm.arxivId)
    if (success) {
      setPaperForm({ doi: '', arxivId: '' })
      setShowAddPaper(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Search and Add Paper */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 flex gap-2">
          <Input
            placeholder="論文を検索..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && onSearch()}
          />
          <Button onClick={onSearch}>
            <SearchIcon className="h-4 w-4" />
          </Button>
        </div>
        
        <Button onClick={() => setShowAddPaper(!showAddPaper)}>
          <PlusIcon className="h-4 w-4 mr-2" />
          論文を追加
        </Button>
      </div>

      {/* Add Paper Form */}
      {showAddPaper && (
        <Card>
          <CardHeader>
            <CardTitle>論文を追加</CardTitle>
            <CardDescription>DOIまたはarXiv IDを入力してください</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddPaper} className="space-y-4">
              <Input
                placeholder="DOI (例: 10.1038/nature12373)"
                value={paperForm.doi}
                onChange={(e) => setPaperForm({...paperForm, doi: e.target.value})}
              />
              <Input
                placeholder="arXiv ID (例: 1706.03762)"
                value={paperForm.arxivId}
                onChange={(e) => setPaperForm({...paperForm, arxivId: e.target.value})}
              />
              <div className="flex gap-2">
                <Button type="submit">追加</Button>
                <Button type="button" variant="outline" onClick={() => setShowAddPaper(false)}>
                  キャンセル
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Papers List */}
      <div className="space-y-4">
        {papers.length === 0 ? (
          <Card>
            <CardContent className="text-center py-8">
              <p className="text-gray-500">論文が見つかりませんでした</p>
            </CardContent>
          </Card>
        ) : (
          papers.map((paper) => (
            <PaperCard 
              key={paper.id} 
              paper={paper} 
              isBookmarked={bookmarks.some(b => b.paper_id === paper.id)}
              onToggleBookmark={onToggleBookmark}
            />
          ))
        )}
      </div>
    </div>
  )
}

function PaperCard({ paper, isBookmarked, onToggleBookmark }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <CardTitle className="text-lg">{paper.title}</CardTitle>
            <CardDescription className="mt-2">
              <div className="text-sm text-gray-600">
                <p><strong>著者:</strong> {paper.authors}</p>
                <p><strong>発行日:</strong> {paper.published_date}</p>
                {paper.journal && <p><strong>ジャーナル:</strong> {paper.journal}</p>}
                {paper.doi && <p><strong>DOI:</strong> {paper.doi}</p>}
                {paper.arxiv_id && <p><strong>arXiv ID:</strong> {paper.arxiv_id}</p>}
              </div>
            </CardDescription>
          </div>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onToggleBookmark(paper.id)}
            className={isBookmarked ? 'text-yellow-600' : 'text-gray-400'}
          >
            <BookmarkIcon className={`h-4 w-4 ${isBookmarked ? 'fill-current' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {paper.abstract && (
            <div>
              <h4 className="font-semibold mb-2">アブストラクト</h4>
              <p className="text-sm text-gray-700">{paper.abstract}</p>
            </div>
          )}
          
          {paper.ai_summary && (
            <div>
              <h4 className="font-semibold mb-2">AI要約</h4>
              <div className="bg-blue-50 p-3 rounded-lg">
                <p className="text-sm text-blue-800">{paper.ai_summary}</p>
              </div>
            </div>
          )}
          
          <div className="flex items-center gap-4 pt-2">
            <Button variant="outline" size="sm">
              <MessageCircleIcon className="h-4 w-4 mr-2" />
              ディスカッション
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function BookmarksPage({ bookmarks, onToggleBookmark }) {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">ブックマーク</h2>
      
      <div className="space-y-4">
        {bookmarks.length === 0 ? (
          <Card>
            <CardContent className="text-center py-8">
              <p className="text-gray-500">ブックマークした論文がありません</p>
            </CardContent>
          </Card>
        ) : (
          bookmarks.map((bookmark) => (
            <PaperCard 
              key={bookmark.paper.id} 
              paper={bookmark.paper} 
              isBookmarked={true}
              onToggleBookmark={onToggleBookmark}
            />
          ))
        )}
      </div>
    </div>
  )
}

export default App

