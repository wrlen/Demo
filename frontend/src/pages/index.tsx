import { useState, useEffect } from 'react'
import Router from 'next/router'

interface Dialogue {
  speaker: string
  text: string
  position: string
}

interface Narration {
  text: string
  position: string
}

interface Action {
  description: string
  position: string
}

interface ScriptResponse {
  dialogues: Dialogue[]
  narrations: Narration[]
  actions: Action[]
  characters: string[]
}

export default function Home() {
  const [inputText, setInputText] = useState('')
  const [script, setScript] = useState<ScriptResponse | null>(null)
  const [projectId, setProjectId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showSidebar, setShowSidebar] = useState(false)
  const [customCharacter, setCustomCharacter] = useState('')
  const [activeTab, setActiveTab] = useState('result')

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (e.clientX > window.innerWidth - 60) {
        setShowSidebar(true)
      } else {
        setShowSidebar(false)
      }
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  const handleSubmit = async () => {
    if (!inputText.trim()) {
      setError('请输入剧本内容')
      return
    }

    setLoading(true)
    setError('')

    try {
      const createResponse = await fetch('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'title=剧本项目&description=自动生成',
      })

      if (!createResponse.ok) {
        throw new Error('创建项目失败')
      }

      const projectData = await createResponse.json()
      const newProjectId = projectData.id

      const scriptResponse = await fetch(`/api/projects/${newProjectId}/script`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ raw_text: inputText }),
      })

      if (!scriptResponse.ok) {
        throw new Error('生成剧本失败')
      }

      const scriptData = await scriptResponse.json()
      setScript(scriptData)
      setProjectId(newProjectId)

      if (scriptData.characters.length > 0) {
        await fetch(`/api/projects/${newProjectId}/characters`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(scriptData.characters),
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '发生未知错误')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateStoryboard = () => {
    if (projectId && script) {
      localStorage.setItem('currentProjectId', projectId)
      localStorage.setItem('currentScript', JSON.stringify(script))
      const scriptData = encodeURIComponent(JSON.stringify(script))
      Router.push(`/storyboard?projectId=${projectId}&scriptData=${scriptData}`)
    }
  }

  const handleAddCharacter = async () => {
    if (!customCharacter.trim() || !projectId) return
    
    try {
      const response = await fetch(`/api/projects/${projectId}/characters`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify([customCharacter.trim()]),
      })
      
      if (response.ok) {
        setScript(prev => prev ? {
          ...prev,
          characters: [...prev.characters, customCharacter.trim()]
        } : null)
        setCustomCharacter('')
      }
    } catch (err) {
      console.error('添加角色失败:', err)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      {/* 背景装饰 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 -left-40 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute -bottom-40 right-1/3 w-72 h-72 bg-pink-500/20 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
        <div className="absolute top-1/3 right-1/4 w-64 h-64 bg-indigo-500/15 rounded-full blur-3xl animate-pulse" style={{animationDelay: '0.5s'}}></div>
        
        {/* 网格背景 */}
        <div className="absolute inset-0 opacity-5">
          <div className="h-full w-full" style={{backgroundImage: 'linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)', backgroundSize: '50px 50px'}}></div>
        </div>
      </div>

      {/* 顶部导航 */}
      <header className="bg-white/5 backdrop-blur-xl border-b border-white/10 sticky top-0 z-40 relative">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-xl flex items-center justify-center text-white font-bold shadow-lg shadow-purple-500/30">
                🎬
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-white via-purple-200 to-white bg-clip-text text-transparent">漫剧自动化工作台</h1>
                <p className="text-xs text-gray-400">AI驱动的剧本创作与分镜生成平台</p>
              </div>
            </div>
            <nav className="flex items-center gap-1">
              <a href="/" className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white/90 font-medium hover:from-blue-500/30 hover:to-purple-500/30 transition-all">剧本输入</a>
              <a href="/storyboard" className="px-4 py-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 font-medium transition-all">分镜管理</a>
              <a href="/characters" className="px-4 py-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 font-medium transition-all">角色管理</a>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero区域 */}
      <div className="relative max-w-7xl mx-auto px-4 py-8 mb-8">
        <div className="text-center">
          <h2 className="text-4xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-4">
            智能剧本解析引擎
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            输入任意格式的文本，AI将自动识别角色、对话、旁白和动作，为您生成结构化的剧本数据
          </p>
          
          {/* 功能标签 */}
          <div className="flex justify-center gap-4 mt-6">
            {['智能识别', '自动分类', '一键生成分镜', '角色管理'].map((tag, index) => (
              <span key={index} className="px-4 py-2 bg-white/5 backdrop-blur-sm rounded-full text-gray-300 text-sm border border-white/10 hover:bg-white/10 transition-all">
                ✨ {tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* 主内容区域 */}
      <main className="max-w-7xl mx-auto px-4 pb-8 relative">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左侧：剧本输入 */}
          <div className="relative">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl blur opacity-30"></div>
            <div className="relative bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden">
              <div className="bg-gradient-to-r from-blue-600/30 to-purple-600/30 px-6 py-4 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold">
                    📄
                  </div>
                  <div>
                    <h2 className="font-semibold text-white">输入剧本文本</h2>
                    <p className="text-xs text-gray-400">支持中文剧本格式，自动识别角色与对话</p>
                  </div>
                </div>
              </div>
              <div className="p-6">
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="请输入剧本内容...&#10;&#10;示例：&#10;少年浑身是血，跪在悬崖边，面前是倒在血泊中的师父。&#10;师父：&quot;你血脉...是被封印的魔尊之力...&quot;&#10;少年握紧剑柄，眼中没有泪水，只有赤红。"
                  className="w-full h-64 p-4 bg-slate-900/50 border border-white/10 rounded-xl resize-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 outline-none transition-all text-white placeholder-gray-500 text-sm"
                />
                {error && (
                  <div className="mt-3 p-3 bg-red-500/20 border border-red-500/30 rounded-xl text-red-400 text-sm flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {error}
                  </div>
                )}
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="mt-4 w-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 hover:from-blue-600 hover:via-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed text-white py-3 rounded-xl font-medium transition-all shadow-lg shadow-purple-500/30 hover:shadow-purple-500/50 hover:-translate-y-0.5"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      AI分析中...
                    </span>
                  ) : (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      生成结构化剧本
                    </span>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* 右侧：生成结果 */}
          <div className="relative">
            <div className="absolute -inset-1 bg-gradient-to-r from-green-500 via-teal-500 to-cyan-500 rounded-2xl blur opacity-30"></div>
            <div className="relative bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden">
              <div className="bg-gradient-to-r from-green-600/30 to-teal-600/30 px-6 py-4 border-b border-white/10">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-semibold text-white">解析结果</h2>
                    <p className="text-xs text-gray-400">{script ? 'AI已成功解析剧本结构' : '等待输入剧本并生成'}</p>
                  </div>
                  {script && (
                    <button
                      onClick={handleGenerateStoryboard}
                      className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-4 py-2 rounded-xl font-medium transition-all shadow-lg shadow-green-500/30 hover:-translate-y-0.5"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      生成分镜
                    </button>
                  )}
                </div>
              </div>
              <div className="p-4">
                {!script ? (
                  <div className="flex flex-col items-center justify-center h-80">
                    <div className="relative">
                      <div className="w-24 h-24 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-full flex items-center justify-center animate-pulse">
                        <svg className="w-12 h-12 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center text-white text-xs font-bold animate-bounce">
                        AI
                      </div>
                    </div>
                    <div className="mt-4 text-gray-400">等待输入剧本</div>
                    <div className="text-sm text-gray-500 mt-1">点击左侧按钮生成结构化剧本</div>
                    
                    {/* 预览示例 */}
                    <div className="mt-6 w-full">
                      <div className="text-xs text-gray-500 mb-2 text-center">💡 输入示例</div>
                      <div className="bg-slate-900/50 rounded-xl p-3 border border-white/5">
                        <p className="text-gray-400 text-xs">少年浑身是血，跪在悬崖边...</p>
                        <p className="text-purple-400 text-xs mt-1">师父："你血脉是被封印的魔尊之力..."</p>
                        <p className="text-gray-400 text-xs mt-1">少年握紧剑柄，眼中没有泪水...</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4 max-h-[520px] overflow-auto pr-2">
                    {/* 统计卡片 */}
                    <div className="grid grid-cols-4 gap-3">
                      {[
                        { label: '角色', value: script.characters.length, color: 'blue', icon: '👥' },
                        { label: '对话', value: script.dialogues.length, color: 'green', icon: '💬' },
                        { label: '旁白', value: script.narrations.length, color: 'purple', icon: '📝' },
                        { label: '动作', value: script.actions.length, color: 'orange', icon: '🎬' },
                      ].map((stat, index) => (
                        <div key={index} className={`bg-gradient-to-br from-${stat.color}-500/20 to-${stat.color}-600/10 rounded-xl p-3 border border-${stat.color}-500/20`}>
                          <div className="text-2xl font-bold text-white">{stat.value}</div>
                          <div className="text-xs text-gray-400">{stat.label}</div>
                        </div>
                      ))}
                    </div>

                    {/* 标签切换 */}
                    <div className="flex gap-2 bg-slate-900/50 rounded-xl p-1">
                      {[
                        { key: 'characters', label: '角色', icon: '👥' },
                        { key: 'dialogues', label: '对话', icon: '💬' },
                        { key: 'narrations', label: '旁白', icon: '📝' },
                        { key: 'actions', label: '动作', icon: '🎬' },
                      ].map((tab) => (
                        <button
                          key={tab.key}
                          onClick={() => setActiveTab(tab.key)}
                          className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-all ${
                            activeTab === tab.key 
                              ? 'bg-white/10 text-white' 
                              : 'text-gray-400 hover:text-white hover:bg-white/5'
                          }`}
                        >
                          {tab.icon} {tab.label}
                        </button>
                      ))}
                    </div>

                    {/* 内容区域 */}
                    <div className="min-h-[200px]">
                      {activeTab === 'characters' && (
                        <div className="space-y-3">
                          {script.characters.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">暂无角色</div>
                          ) : (
                            <>
                              {script.characters.map((char, index) => (
                                <div key={index} className="flex items-center gap-3 p-3 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl border border-blue-500/20 hover:border-blue-500/40 transition-all hover:-translate-x-0.5">
                                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold shadow-lg">
                                    {char.name.charAt(0)}
                                  </div>
                                  <div className="flex-1">
                                    <div className="text-white font-medium">{char.name}</div>
                                    <div className="text-xs text-gray-400">{char.description || '已识别角色'}</div>
                                  </div>
                                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                  </svg>
                                </div>
                              ))}
                              
                              {/* 添加角色 */}
                              <div className="p-3 bg-white/5 rounded-xl border border-dashed border-white/20 hover:border-white/30 transition-all">
                                <div className="flex gap-2">
                                  <input
                                    type="text"
                                    value={customCharacter}
                                    onChange={(e) => setCustomCharacter(e.target.value)}
                                    placeholder="添加新角色..."
                                    className="flex-1 px-3 py-2 bg-slate-900/50 border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 outline-none"
                                    onKeyPress={(e) => e.key === 'Enter' && handleAddCharacter()}
                                  />
                                  <button
                                    onClick={handleAddCharacter}
                                    className="px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-blue-500/30"
                                  >
                                    添加
                                  </button>
                                </div>
                              </div>
                            </>
                          )}
                        </div>
                      )}

                      {activeTab === 'dialogues' && (
                        <div className="space-y-3">
                          {script.dialogues.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">暂无对话</div>
                          ) : (
                            script.dialogues.map((dialogue, index) => (
                              <div key={index} className="p-4 bg-gradient-to-r from-green-500/10 to-emerald-500/10 rounded-xl border border-green-500/20 hover:border-green-500/40 transition-all hover:-translate-x-0.5">
                                <div className="flex items-start gap-3">
                                  <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                                    {dialogue.speaker.charAt(0)}
                                  </div>
                                  <div className="flex-1">
                                    <div className="text-green-400 font-medium text-sm">{dialogue.speaker}</div>
                                    <div className="text-white/90 text-sm mt-1">{dialogue.text}</div>
                                  </div>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      )}

                      {activeTab === 'narrations' && (
                        <div className="space-y-3">
                          {script.narrations.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">暂无旁白</div>
                          ) : (
                            script.narrations.map((narration, index) => (
                              <div key={index} className="p-4 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-xl border border-purple-500/20 hover:border-purple-500/40 transition-all hover:-translate-x-0.5">
                                <div className="flex items-start gap-3">
                                  <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                                    N
                                  </div>
                                  <div className="text-white/90 text-sm">{narration.text}</div>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      )}

                      {activeTab === 'actions' && (
                        <div className="space-y-3">
                          {script.actions.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">暂无动作</div>
                          ) : (
                            script.actions.map((action, index) => (
                              <div key={index} className="p-4 bg-gradient-to-r from-orange-500/10 to-yellow-500/10 rounded-xl border border-orange-500/20 hover:border-orange-500/40 transition-all hover:-translate-x-0.5">
                                <div className="flex items-start gap-3">
                                  <div className="w-8 h-8 bg-gradient-to-br from-orange-500 to-yellow-600 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                                    A
                                  </div>
                                  <div className="text-white/90 text-sm">{action.description}</div>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* 右侧悬浮功能按钮栏 */}
      <div 
        className={`fixed right-0 top-1/2 -translate-y-1/2 z-50 transition-all duration-300 ${
          showSidebar ? 'translate-x-0' : 'translate-x-[calc(100%-48px)]'
        }`}
      >
        <div className="flex items-center bg-slate-800/80 backdrop-blur-xl shadow-xl rounded-l-2xl border border-white/10 border-r-0">
          {/* 展开按钮 */}
          <button className="w-12 h-12 flex items-center justify-center bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-l-xl transition-all">
            <svg className={`w-5 h-5 transition-transform duration-300 ${showSidebar ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
          
          {/* 功能按钮 */}
          <div className="flex flex-col gap-3 p-4">
            <button 
              className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 flex items-center justify-center text-white shadow-lg shadow-blue-500/30 transition-all hover:-translate-y-1" 
              title="角色管理"
              onClick={() => Router.push('/characters')}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </button>
            <button 
              className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 flex items-center justify-center text-white shadow-lg shadow-purple-500/30 transition-all hover:-translate-y-1" 
              title="分镜管理"
              onClick={() => Router.push('/storyboard')}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
              </svg>
            </button>

            <button 
              className="w-12 h-12 rounded-xl bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-all hover:-translate-y-1" 
              title="设置"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
