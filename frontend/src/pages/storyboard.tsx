import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'

interface Shot {
  shot_id: number
  scene_type: string
  duration: number
  camera_movement: string | null
  visual_description: string
  character_emotion: string | null
  dialogue: string
  narration: string
  image_url: string | null
}

interface Character {
  id: string
  name: string
  description: string
  references: { id: string; view_type: string; image_url: string }[]
}

interface StoryboardResponse {
  shots: Shot[]
}

export default function Storyboard() {
  const router = useRouter()
  const { projectId: queryProjectId, scriptData } = router.query
  const [projectId, setProjectId] = useState<string | null>(null)
  const [storyboard, setStoryboard] = useState<StoryboardResponse | null>(null)
  const [characters, setCharacters] = useState<Character[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [editingShot, setEditingShot] = useState<number | null>(null)
  const [editData, setEditData] = useState<Partial<Shot>>({})
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null)
  const [generatingCharacter, setGeneratingCharacter] = useState<string | null>(null)
  const [showCharacterPanel, setShowCharacterPanel] = useState(true)
  const [expandedPromptIds, setExpandedPromptIds] = useState<string[]>([])

  const shotsPerPage = 4

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      alert('提示词已复制到剪贴板')
    } catch (err) {
      console.error('复制失败:', err)
    }
  }

  useEffect(() => {
    const pid = queryProjectId as string || localStorage.getItem('currentProjectId')
    if (!pid) {
      setError('缺少项目ID')
      setLoading(false)
      return
    }
    setProjectId(pid)

    const cachedScript = localStorage.getItem('currentScript')
    if (cachedScript) {
      try {
        const parsedScript = JSON.parse(cachedScript)
        fetchStoryboardWithScript(parsedScript, pid)
      } catch {
        fetchStoryboardDirectly(pid)
      }
    } else {
      fetchStoryboardDirectly(pid)
    }

    fetchCharacters(pid)
  }, [queryProjectId])

  const fetchStoryboardDirectly = async (pid: string) => {
    try {
      const response = await fetch(`/api/projects/${pid}/storyboard`)
      if (!response.ok) throw new Error('获取分镜失败')
      const data = await response.json()
      setStoryboard(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '发生未知错误')
    } finally {
      setLoading(false)
    }
  }

  const fetchStoryboardWithScript = async (parsedScript: any, pid: string) => {
    try {
      const response = await fetch(`/api/projects/${pid}/storyboard`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsedScript),
      })
      if (!response.ok) throw new Error('生成分镜失败')
      const data = await response.json()
      setStoryboard(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '发生未知错误')
    } finally {
      setLoading(false)
    }
  }

  const fetchCharacters = async (pid: string) => {
    try {
      const response = await fetch(`/api/projects/${pid}/characters`)
      if (!response.ok) throw new Error('获取角色失败')
      const data = await response.json()
      setCharacters(data.characters || [])
    } catch (err) {
      console.log('获取角色列表失败:', err)
    }
  }

  const handleEditStart = (shot: Shot) => {
    setEditingShot(shot.shot_id)
    setEditData({ ...shot })
  }

  const handleEditSave = async (shotId: number) => {
    try {
      const response = await fetch(`/api/projects/${projectId}/storyboard/${shotId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editData),
      })
      if (!response.ok) throw new Error('更新分镜失败')
      const data = await response.json()
      setStoryboard(data)
      setEditingShot(null)
    } catch (err) {
      alert(err instanceof Error ? err.message : '发生未知错误')
    }
  }

  const handleGenerateCharacter = async (characterId: string) => {
    setGeneratingCharacter(characterId)
    try {
      const response = await fetch(`/api/projects/${projectId}/characters/${characterId}/generate`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('生成三视图失败')
      await fetchCharacters(projectId!)
    } catch (err) {
      alert(err instanceof Error ? err.message : '发生未知错误')
    } finally {
      setGeneratingCharacter(null)
    }
  }

  const goBack = () => {
    router.push('/')
  }

  const getCurrentShots = () => {
    if (!storyboard) return []
    const start = (currentPage - 1) * shotsPerPage
    const end = start + shotsPerPage
    return storyboard.shots.slice(start, end)
  }

  const totalPages = () => {
    if (!storyboard) return 1
    return Math.ceil(storyboard.shots.length / shotsPerPage)
  }

  const getCharacterPrompt = (character: Character) => {
    const description = character.description || ''
    const name = character.name || ''
    
    let style = ''
    let age = '约25-30岁'
    let pose = '全身正面站立，正对镜头'
    let features = '发型精致，面容清晰，五官精致立体'
    let clothing = '服装精致'
    let skin = '皮肤白皙'
    let background = '纯白背景'
    let expression = '表情自然'
    let lighting = '柔和自然光'
    
    // 角色类型关键词映射 - 增加更多差异化配置
    const roleTypes = [
      { keywords: ['地府', '孟婆', '无常', '阴间', '阎王', '判官', '鬼差', '亡灵'], 
        age: '外表约30-40岁，不老容颜', style: '暗黑风格，神秘诡异', skin: '皮肤苍白', background: '暗黑背景，烟雾缭绕，阴森恐怖', 
        features: '面容冷峻，眼神深邃，五官立体分明', clothing: '身着黑袍，神秘莫测，衣袂飘飘',
        pose: '肃立姿态，双手交叠', expression: '表情肃穆，眼神空洞', lighting: '冷色调暗光' },
      { keywords: ['书生', '儒雅', '温文尔雅', '夫子', '教书'], 
        age: '约20-28岁', style: '古风儒雅风格，书卷气', clothing: '身着青色长袍，书生装束，手持书卷', 
        features: '面容清秀，气质文雅，眉清目秀', pose: '手持书卷站立，温文尔雅',
        expression: '神情专注，温文尔雅', lighting: '书房柔和光线', background: '书房背景，笔墨纸砚' },
      { keywords: ['将军', '威武', '勇猛', '侠客', '剑客', '大侠', '豪杰'], 
        age: '约25-35岁', style: '武侠风格，英武霸气，江湖气息', clothing: '身着银色铠甲/黑色劲装，英姿飒爽', 
        features: '面容刚毅，眼神坚定，英气逼人', pose: '英姿飒爽站立，手握长剑/兵器',
        expression: '神情坚毅，目光锐利', lighting: '战场硬朗光线', background: '战场/山林背景' },
      { keywords: ['少女', '清纯', '可爱', '天真', '活泼'], 
        style: '清新甜美风格，青春洋溢', age: '约18-22岁', features: '面容清纯，眼神灵动，甜美可爱', 
        skin: '皮肤白皙细腻，吹弹可破', clothing: '身着粉色连衣裙/古装襦裙',
        pose: '轻盈站立，姿态优美', expression: '笑容灿烂，天真无邪', lighting: '明亮柔和光线', 
        background: '花园/竹林背景，清新自然' },
      { keywords: ['老人', '年长者', '老者', '老翁', '老妇'], 
        age: '约60-70岁', features: '面容慈祥，白发苍苍，皱纹深刻', skin: '皮肤略显皱纹，岁月痕迹', 
        clothing: '身着朴素布衣/长袍', pose: '端坐姿态，手持拐杖',
        expression: '和蔼可亲，眼神慈祥', lighting: '温暖柔和光线', background: '室内/庭院背景' },
      { keywords: ['公子', '风度翩翩', '少爷', '贵公子'], 
        age: '约20-28岁', style: '古风贵公子风格，风流倜傥', clothing: '身着锦袍，腰佩玉带，风度翩翩', 
        features: '面容俊朗，气质高雅，玉树临风', pose: '潇洒站立，折扇轻摇',
        expression: '潇洒自信，风度不凡', lighting: '优雅室内光线', background: '庭院/书房背景' },
      { keywords: ['小姐', '大家闺秀', '千金', '郡主', '公主'], 
        style: '古风大家闺秀风格，端庄典雅', age: '约18-25岁', clothing: '身着华丽古装长裙，配饰精美', 
        features: '面容秀美，气质温婉，大家闺秀', pose: '优雅端坐，仪态万方',
        expression: '端庄娴静，温婉可人', lighting: '闺房柔和光线', background: '闺房/花园背景' },
      { keywords: ['道士', '道长', '仙长', '修行者'], 
        age: '外表约40-50岁，仙风道骨', style: '仙侠风格，仙风道骨，超凡脱俗', clothing: '身着蓝色道袍，手持拂尘', 
        features: '面容清癯，仙风道骨，鹤发童颜', pose: '拂尘轻挥，仙风道骨',
        expression: '超然物外，仙气飘飘', lighting: '仙雾缭绕光线', background: '云雾缭绕，仙山背景' },
      { keywords: ['和尚', '僧人', '大师', '方丈'], 
        age: '约30-50岁', style: '禅意风格，清净脱俗，佛法庄严', clothing: '身着黄色僧袍，光头', 
        features: '面容慈悲，宝相庄严，耳垂饱满', pose: '双手合十，禅定姿态',
        expression: '慈悲祥和，宁静致远', lighting: '寺庙佛光', background: '寺庙背景，香火缭绕' },
      { keywords: ['魔女', '妖女', '狐妖', '蛇妖', '妖精'], 
        age: '外表约20-25岁，魅惑动人', style: '魅惑风格，妖娆动人，妖气十足', clothing: '身着华丽妖装，妩媚动人', 
        features: '面容妖艳，眼神勾人，狐媚动人', skin: '皮肤白皙，魅惑诱人',
        pose: '妖娆姿态，媚态百出', expression: '眼神魅惑，勾人心魄', lighting: '妖异紫色光线', 
        background: '幽暗森林，妖气弥漫' },
      { keywords: ['皇帝', '帝王', '君主', '陛下'], 
        age: '约30-50岁', style: '帝王风格，威严霸气，九五之尊', clothing: '身着明黄龙袍，头戴皇冠，佩戴玉玺', 
        features: '面容威严，不怒自威，龙行虎步', pose: '龙椅端坐，君临天下',
        expression: '威严庄重，帝王之气', lighting: '金碧辉煌光线', background: '金碧辉煌的宫殿，龙椅' },
      { keywords: ['皇后', '太后', '贵妃', '妃子'], 
        age: '约25-40岁', style: '宫廷风格，华贵典雅，母仪天下', clothing: '身着华丽宫装，头戴凤冠，珠翠环绕', 
        features: '面容端庄，气质高贵，仪态万方', pose: '凤椅端坐，端庄典雅',
        expression: '母仪天下，端庄大气', lighting: '宫廷华丽光线', background: '宫廷背景，富丽堂皇' },
      { keywords: ['刺客', '杀手', '暗影'], 
        age: '约20-30岁', style: '暗黑风格，神秘冷酷，致命杀机', clothing: '身着黑衣劲装，蒙面，佩戴暗器', 
        features: '面容冷峻，眼神锐利，杀气腾腾', pose: '持武器半蹲，姿态矫健',
        expression: '冷酷无情，眼神犀利', lighting: '阴暗冷光', background: '黑暗背景，阴影重重' },
      { keywords: ['医生', '医者', '郎中', '大夫'], 
        age: '约30-50岁', style: '古风医者风格，悬壶济世', clothing: '身着素色布衣，背着药箱，手持药锄', 
        features: '面容和蔼，眼神慈祥，医者仁心', pose: '手持药草，温和站立',
        expression: '和蔼可亲，医者仁心', lighting: '药庐温暖光线', background: '药庐背景，草药飘香' },
      { keywords: ['商人', '掌柜', '老板'], 
        age: '约30-50岁', style: '古风商人风格，精明干练', clothing: '身着锦缎长袍，手持算盘，腰缠万贯', 
        features: '面容精明，眼神锐利，商人气质', pose: '手持算盘，精明站立',
        expression: '精明干练，生意盎然', lighting: '商铺明亮光线', background: '商铺背景，琳琅满目' },
      { keywords: ['小孩', '孩童', '童子', '少年'], 
        age: '约10-16岁', features: '面容稚嫩，眼神纯真，天真活泼', 
        clothing: '身着童装，天真无邪', pose: '活泼站立，充满童趣',
        expression: '天真烂漫，活泼可爱', lighting: '明亮童趣光线', background: '庭院/学堂背景' },
      { keywords: ['中年', '成熟', '稳重'], 
        age: '约35-50岁', features: '面容成熟，气质稳重，沉稳内敛', 
        clothing: '身着得体服饰，成熟稳重', pose: '稳重站立，自信从容',
        expression: '沉稳内敛，成熟稳重', lighting: '办公室/书房光线', background: '稳重背景' },
      { keywords: ['青年', '朝气蓬勃'], 
        age: '约20-28岁', features: '面容阳光，充满活力，青春洋溢', 
        clothing: '身着时尚服饰，青春活力', pose: '活力站立，朝气蓬勃',
        expression: '阳光开朗，充满朝气', lighting: '明亮阳光', background: '现代都市背景' },
      { keywords: ['温柔', '善良', '体贴'], 
        features: '面容温柔，眼神和善，亲和力强', style: '温柔风格，亲和力',
        expression: '温柔微笑，亲和力强', lighting: '柔和温暖光线' },
      { keywords: ['暴躁', '易怒', '凶狠'], 
        features: '面容凶狠，眼神凌厉，气势逼人', style: '凶戾风格，霸气外露',
        expression: '怒目圆睁，气势汹汹', lighting: '强烈对比光线' },
      { keywords: ['智慧', '深沉', '睿智'], 
        features: '面容沉稳，眼神深邃，智慧光芒', style: '智者风格，深不可测',
        expression: '深思熟虑，智慧光芒', lighting: '书房柔和光线', background: '书房/图书馆背景' },
      { keywords: ['活泼', '开朗', '乐观'], 
        features: '面容阳光，笑容灿烂，活力四射', style: '活泼风格，阳光开朗',
        expression: '笑容满面，活力四射', lighting: '明亮欢快光线', background: '户外阳光背景' },
      { keywords: ['冷酷', '冷漠', '孤傲'], 
        features: '面容冷峻，眼神冰冷，拒人千里', style: '冷酷风格，孤高冷傲',
        expression: '面无表情，冷酷无情', lighting: '冷色调光线', background: '冷峻背景' },
      { keywords: ['红衣', '红袍'], 
        clothing: '身着红色衣袍，鲜艳夺目，热情似火', style: '红衣风格，热情奔放',
        background: '红色主题背景', lighting: '温暖热烈光线' },
      { keywords: ['白衣', '白袍'], 
        clothing: '身着白色衣袍，纯洁素雅，仙气飘飘', style: '白衣风格，纯洁高雅',
        background: '白色纯净背景', lighting: '明亮纯净光线' },
      { keywords: ['黑衣', '黑袍'], 
        clothing: '身着黑色衣袍，神秘深沉，冷酷无情', style: '暗黑风格，神秘冷酷',
        background: '黑暗神秘背景', lighting: '阴暗冷光' },
    ]
    
    // 检查角色名称中的关键词
    const fullText = (description + ' ' + name).toLowerCase()
    
    // 应用匹配到的角色类型
    for (const roleType of roleTypes) {
      if (roleType.keywords.some(kw => fullText.includes(kw.toLowerCase()))) {
        if (roleType.style) style = roleType.style
        if (roleType.age) age = roleType.age
        if (roleType.pose) pose = roleType.pose
        if (roleType.features) features = roleType.features
        if (roleType.clothing) clothing = roleType.clothing
        if (roleType.skin) skin = roleType.skin
        if (roleType.background) background = roleType.background
        if (roleType.expression) expression = roleType.expression
        if (roleType.lighting) lighting = roleType.lighting
      }
    }
    
    // 如果没有匹配到任何风格，使用默认风格
    if (!style) {
      // 根据名称长度和字符判断性别
      const femaleIndicators = ['女', '娘', '妹', '姐', '姑', '姨', '婆', '妃', '后', '公主']
      const isFemale = femaleIndicators.some(ind => name.includes(ind))
      if (isFemale) {
        style = '，唯美风格'
      }
    }
    
    // 根据角色类型生成差异化的提示词结尾
    const styleSuffix = style ? `，${style}` : ''
    
    return `${character.name}，真人写实，${age}，${description}${styleSuffix}，${pose}，${features}，${clothing}，${skin}，${expression}，${lighting}，画面精美细致，影视级光影质感，${background}，高清8K画质，超写实渲染`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden flex">
      {/* 背景装饰 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 -left-40 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute -bottom-40 right-1/3 w-72 h-72 bg-pink-500/20 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
        <div className="absolute inset-0 opacity-5">
          <div className="h-full w-full" style={{backgroundImage: 'linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)', backgroundSize: '50px 50px'}}></div>
        </div>
      </div>

      {/* 左侧：分镜卡片区域 */}
      <div className="flex-1 flex flex-col relative z-10">
        {/* 顶部导航栏 */}
        <header className="bg-white/5 backdrop-blur-xl border-b border-white/10 sticky top-0 z-40">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button 
                  onClick={goBack} 
                  className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors group"
                >
                  <svg className="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  <span className="font-medium">返回主页</span>
                </button>
                <div className="h-6 w-px bg-white/10"></div>
                <h1 className="text-lg font-semibold bg-gradient-to-r from-white via-purple-200 to-white bg-clip-text text-transparent">漫剧工作台 - 分镜编辑</h1>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 bg-white/5 backdrop-blur-sm rounded-lg px-3 py-2 border border-white/10">
                  <span className="text-sm text-gray-400">剧集</span>
                  <select className="bg-transparent border-none outline-none text-sm font-medium text-white">
                    <option>第1集：序幕</option>
                  </select>
                </div>
                <div className="flex items-center gap-2 bg-white/5 backdrop-blur-sm rounded-lg px-3 py-2 border border-white/10">
                  <span className="text-sm text-gray-400">场景</span>
                  <select className="bg-transparent border-none outline-none text-sm font-medium text-white">
                    <option>1</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* 分镜内容区域 */}
        <div className="flex-1 p-6 overflow-auto">
          {loading && (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="relative">
                <div className="w-16 h-16 border-4 border-blue-200 rounded-full animate-spin border-t-blue-500"></div>
                <div className="absolute inset-0 w-16 h-16 border-4 border-transparent rounded-full animate-ping border-t-blue-400"></div>
              </div>
              <div className="mt-4 text-lg font-medium text-gray-400">生成分镜中...</div>
            </div>
          )}

          {error && (
            <div className="max-w-2xl mx-auto mt-8 p-4 bg-red-500/20 backdrop-blur-sm border border-red-500/30 rounded-xl text-red-400">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{error}</span>
              </div>
            </div>
          )}

          {storyboard && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {getCurrentShots().map((shot) => (
                  <div 
                    key={shot.shot_id} 
                    className="relative"
                  >
                    <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl blur opacity-30"></div>
                    <div className="relative bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden hover:border-white/20 transition-all duration-300">
                      {/* 分镜头部 */}
                      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-blue-600/30 to-indigo-600/30 border-b border-white/10">
                        <div className="flex items-center gap-3">
                          <div className="relative">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-blue-500/30">
                              {shot.shot_id}
                            </div>
                            <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-slate-800"></div>
                          </div>
                          <div>
                            <div className="font-semibold text-white">分镜 {shot.shot_id}</div>
                            <div className="text-xs text-gray-400">时长: {shot.duration}s</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="px-3 py-1 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full text-xs font-medium text-gray-300">
                            {shot.scene_type}
                          </span>
                        </div>
                      </div>

                      {/* 分镜内容 */}
                      <div className="grid grid-cols-2">
                        {/* 画面预览 */}
                        <div className="relative aspect-video bg-gradient-to-br from-slate-900/50 to-slate-800/50">
                          {shot.image_url ? (
                            <img
                              src={shot.image_url}
                              alt={`镜头 ${shot.shot_id}`}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex flex-col items-center justify-center text-gray-500">
                              <svg className="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              <span className="text-sm">暂无图片</span>
                            </div>
                          )}
                          {/* 帧标记 */}
                          <div className="absolute bottom-3 right-3 flex gap-1.5">
                            <span className="px-2 py-1 bg-black/60 backdrop-blur-sm text-white text-xs rounded-md flex items-center gap-1">
                              <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                              首帧
                            </span>
                            <span className="px-2 py-1 bg-black/60 backdrop-blur-sm text-white text-xs rounded-md flex items-center gap-1">
                              <span className="w-2 h-2 bg-red-400 rounded-full"></span>
                              尾帧
                            </span>
                          </div>
                        </div>

                        {/* 分镜信息 */}
                        <div className="p-4">
                          {editingShot === shot.shot_id ? (
                            <div className="space-y-3">
                              <div className="grid grid-cols-2 gap-2">
                                <input
                                  type="text"
                                  value={editData.scene_type || ''}
                                  onChange={(e) => setEditData({ ...editData, scene_type: e.target.value })}
                                  className="p-2 bg-white/10 border border-white/20 rounded-lg text-sm text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                                  placeholder="景别"
                                />
                                <input
                                  type="number"
                                  step="0.1"
                                  value={editData.duration || 0}
                                  onChange={(e) => setEditData({ ...editData, duration: parseFloat(e.target.value) })}
                                  className="p-2 bg-white/10 border border-white/20 rounded-lg text-sm text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                                  placeholder="时长"
                                />
                              </div>
                              <textarea
                                value={editData.visual_description || ''}
                                onChange={(e) => setEditData({ ...editData, visual_description: e.target.value })}
                                className="w-full p-2 bg-white/10 border border-white/20 rounded-lg text-sm text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none h-20 resize-none"
                                placeholder="画面描述"
                              />
                              <div className="flex gap-2">
                                <button
                                  onClick={() => handleEditSave(shot.shot_id)}
                                  className="flex-1 bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded-lg text-sm font-medium transition-colors">保存</button>
                                <button
                                  onClick={() => setEditingShot(null)}
                                  className="flex-1 bg-white/10 hover:bg-white/20 text-gray-300 py-2 px-4 rounded-lg text-sm font-medium transition-colors">取消</button>
                              </div>
                            </div>
                          ) : (
                            <>
                              {/* 镜头运动 */}
                              {shot.camera_movement && (
                                <div className="flex items-center gap-2 mb-3">
                                  <span className="text-xs text-gray-500 font-medium">镜头</span>
                                  <span className="px-2.5 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs font-medium">
                                    {shot.camera_movement}
                                  </span>
                                </div>
                              )}

                              {/* 画面描述 */}
                              <div className="mb-3">
                                <div className="text-xs text-gray-500 font-medium mb-1">画面描述</div>
                                <p className="text-sm text-gray-300 line-clamp-3 leading-relaxed">{shot.visual_description}</p>
                              </div>

                              {/* 角色情绪 */}
                              {shot.character_emotion && (
                                <div className="mb-3">
                                  <span className="text-xs text-gray-500 font-medium">情绪</span>
                                  <span className="px-2.5 py-1 bg-purple-500/20 text-purple-400 rounded-full text-xs font-medium ml-2">
                                    {shot.character_emotion}
                                  </span>
                                </div>
                              )}

                              {/* 对白 */}
                              {shot.dialogue && (
                                <div className="p-3 bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30 rounded-xl mb-2">
                                  <div className="text-xs font-semibold text-green-400 mb-1">对白</div>
                                  <p className="text-sm text-green-300">{shot.dialogue}</p>
                                </div>
                              )}

                              {/* 旁白 */}
                              {shot.narration && (
                                <div className="p-3 bg-gradient-to-r from-purple-500/20 to-indigo-500/20 border border-purple-500/30 rounded-xl mb-3">
                                  <div className="text-xs font-semibold text-purple-400 mb-1">旁白</div>
                                  <p className="text-sm text-purple-300">{shot.narration}</p>
                                </div>
                              )}

                              {/* 操作按钮 */}
                              <div className="flex gap-1.5">
                                <button className="flex-1 px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-xs font-medium text-gray-400 transition-colors">操作</button>
                                <button className="flex-1 px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-xs font-medium text-gray-400 transition-colors">选取</button>
                                <button className="flex-1 px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-xs font-medium text-gray-400 transition-colors">二改</button>
                                <button
                                  onClick={() => handleEditStart(shot)}
                                  className="flex-1 px-3 py-2 bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white rounded-lg text-xs font-medium transition-colors shadow-lg shadow-blue-500/30"
                                >编辑</button>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* 分页 */}
              <div className="flex items-center justify-center gap-4 mt-8">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-5 py-2.5 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center gap-2 text-gray-300"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  上一页
                </button>
                <div className="flex items-center gap-2">
                  {Array.from({ length: totalPages() }, (_, i) => (
                    <button
                      key={i + 1}
                      onClick={() => setCurrentPage(i + 1)}
                      className={`w-9 h-9 rounded-lg font-medium transition-all ${
                        currentPage === i + 1
                          ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30'
                          : 'bg-white/5 border border-white/10 text-gray-400 hover:bg-white/10'
                      }`}
                    >
                      {i + 1}
                    </button>
                  ))}
                </div>
                <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages(), p + 1))}
                  disabled={currentPage === totalPages()}
                  className="px-5 py-2.5 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center gap-2 text-gray-300"
                >
                  下一页
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* 中间：角色资产面板 */}
      <div className={`${showCharacterPanel ? 'w-80' : 'w-0'} transition-all duration-300 overflow-hidden flex flex-col bg-white/5 backdrop-blur-xl border-l border-white/10 relative z-10`}>
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
          <h2 className="font-semibold text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            人物资产
          </h2>
          <button 
            onClick={() => setShowCharacterPanel(false)}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-auto p-4 space-y-4">
          {characters.map((character) => (
            <div
              key={character.id}
              className={`bg-white/5 backdrop-blur-sm rounded-xl border-2 p-3 cursor-pointer transition-all hover:shadow-lg ${
                selectedCharacter?.id === character.id 
                  ? 'border-blue-500 shadow-lg shadow-blue-500/20' 
                  : 'border-white/10 hover:border-white/20'
              }`}
              onClick={() => setSelectedCharacter(character)}
            >
              {/* 角色名称 */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-emerald-500 rounded-lg flex items-center justify-center text-white font-bold text-sm shadow-sm">
                    {character.name.charAt(0)}
                  </div>
                  <span className="font-semibold text-white">{character.name}</span>
                </div>
                <button className="p-1 hover:bg-white/10 rounded-md transition-colors text-gray-400 hover:text-gray-300">
                  ✕
                </button>
              </div>

              {/* 角色三视图 */}
              <div className="flex gap-2 mb-3">
                {['front', 'side', 'back'].map((view) => {
                  const ref = character.references.find(r => r.view_type === view)
                  return (
                    <div key={view} className="flex-1">
                      <div className="text-xs text-gray-500 mb-1 text-center">
                        {view === 'front' ? '正面' : view === 'side' ? '侧面' : '背面'}
                      </div>
                      <div className="aspect-[3/4] bg-slate-900/50 rounded-lg overflow-hidden flex items-center justify-center border border-white/5">
                        {ref && ref.image_url ? (
                          <img
                            src={ref.image_url}
                            alt={view}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <span className="text-gray-500 text-xs">暂无</span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* 提示词 */}
              <div className="bg-white/5 rounded-lg p-2 mb-3 border border-white/5">
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs text-gray-500 font-medium">画面提示词</div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => copyToClipboard(getCharacterPrompt(character))}
                      className="p-1 hover:bg-white/10 rounded transition-colors"
                      title="复制提示词"
                    >
                      <svg className="w-3.5 h-3.5 text-gray-400 hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => {
                        const expandedIds = [...expandedPromptIds];
                        const index = expandedIds.indexOf(character.id);
                        if (index === -1) {
                          expandedIds.push(character.id);
                        } else {
                          expandedIds.splice(index, 1);
                        }
                        setExpandedPromptIds(expandedIds);
                      }}
                      className="p-1 hover:bg-white/10 rounded transition-colors"
                      title={expandedPromptIds.includes(character.id) ? '收起' : '展开'}
                    >
                      <svg className={`w-3.5 h-3.5 text-gray-400 hover:text-white transition-transform ${expandedPromptIds.includes(character.id) ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  </div>
                </div>
                <p className={`text-xs text-gray-400 transition-all duration-300 ${expandedPromptIds.includes(character.id) ? '' : 'line-clamp-3'}`}>
                  {getCharacterPrompt(character)}
                </p>
              </div>

              {/* 操作按钮 */}
              <div className="flex items-center justify-between">
                <div className="flex gap-1.5">
                  <button className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-xs font-medium text-gray-400 hover:bg-white/10 transition-colors">选取</button>
                  <button className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-xs font-medium text-gray-400 hover:bg-white/10 transition-colors">展示</button>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleGenerateCharacter(character.id)
                  }}
                  disabled={generatingCharacter === character.id}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium text-white transition-all ${
                    generatingCharacter === character.id
                      ? 'bg-gray-600 cursor-not-allowed'
                      : 'bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 shadow-lg shadow-green-500/30'
                  }`}
                >
                  {generatingCharacter === character.id ? '生成中...' : '生成图片'}
                </button>
              </div>
            </div>
          ))}

          {characters.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500">
              <svg className="w-16 h-16 mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <div className="font-medium text-gray-400">暂无角色</div>
              <div className="text-sm text-gray-500">请先在剧本页面创建角色</div>
            </div>
          )}
        </div>
      </div>

      {/* 右侧：功能按钮面板 */}
      <div className="w-16 bg-white/5 backdrop-blur-xl border-l border-white/10 flex flex-col items-center py-4 gap-2 relative z-10">
        {/* 展开角色面板按钮 */}
        {!showCharacterPanel && (
          <button
            onClick={() => setShowCharacterPanel(true)}
            className="w-10 h-10 rounded-xl bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors group"
            title="角色资产"
          >
            <svg className="w-5 h-5 text-gray-400 group-hover:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
        )}

        <div className="w-6 h-px bg-white/10 my-2"></div>

        {/* 角色管理 */}
        <button 
          onClick={() => router.push(`/characters?projectId=${projectId}`)}
          className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 flex items-center justify-center transition-all shadow-lg shadow-blue-500/30 group" 
          title="角色管理"
        >
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </button>

        {/* 分镜管理 */}
        <button 
          onClick={() => window.location.reload()}
          className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 flex items-center justify-center transition-all shadow-lg shadow-purple-500/30 group" 
          title="刷新分镜"
        >
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
          </svg>
        </button>

        {/* 设置 */}
        <button className="w-10 h-10 rounded-xl bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors group" title="设置">
          <svg className="w-5 h-5 text-gray-400 group-hover:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </div>
    </div>
  )
}
