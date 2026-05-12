import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'

interface Character {
  id: string
  name: string
  description: string
  references: { id: string; view_type: string; image_url: string }[]
}

export default function Characters() {
  const router = useRouter()
  const { projectId } = router.query
  const [characters, setCharacters] = useState<Character[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [generatingId, setGeneratingId] = useState<string | null>(null)
  const [expandedPromptIds, setExpandedPromptIds] = useState<string[]>([])

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      alert('提示词已复制到剪贴板')
    } catch (err) {
      console.error('复制失败:', err)
    }
  }

  useEffect(() => {
    const pid = projectId as string || localStorage.getItem('currentProjectId')
    if (!pid) {
      setError('缺少项目ID')
      setLoading(false)
      return
    }

    fetchCharacters(pid)
  }, [projectId])

  const fetchCharacters = async (pid: string) => {
    try {
      const response = await fetch(`/api/projects/${pid}/characters`)
      if (!response.ok) throw new Error('获取角色列表失败')
      const data = await response.json()
      setCharacters(data.characters || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : '发生未知错误')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateReferences = async (characterId: string) => {
    setGeneratingId(characterId)
    try {
      const pid = projectId as string || localStorage.getItem('currentProjectId')
      const response = await fetch(`/api/projects/${pid}/characters/${characterId}/generate`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('生成三视图失败')
      await fetchCharacters(pid)
    } catch (err) {
      alert(err instanceof Error ? err.message : '发生未知错误')
    } finally {
      setGeneratingId(null)
    }
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

  const goBack = () => {
    router.push('/')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/2 -left-40 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
        <div className="absolute -bottom-40 right-1/3 w-72 h-72 bg-pink-500/20 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
        <div className="absolute inset-0 opacity-5">
          <div className="h-full w-full" style={{backgroundImage: 'linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)', backgroundSize: '50px 50px'}}></div>
        </div>
      </div>

      <header className="bg-white/5 backdrop-blur-xl border-b border-white/10 sticky top-0 z-40 relative">
        <div className="max-w-7xl mx-auto px-4 py-4">
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
              <h1 className="text-lg font-semibold bg-gradient-to-r from-white via-purple-200 to-white bg-clip-text text-transparent">角色管理</h1>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1.5 bg-white/5 backdrop-blur-sm rounded-full text-sm text-gray-300 border border-white/10">
                {characters.length} 位角色
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 relative">
        {loading && (
          <div className="flex flex-col items-center justify-center h-96">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-blue-200 rounded-full animate-spin border-t-blue-500"></div>
              <div className="absolute inset-0 w-16 h-16 border-4 border-transparent rounded-full animate-ping border-t-blue-400"></div>
            </div>
            <div className="mt-4 text-lg font-medium text-gray-400">加载角色中...</div>
          </div>
        )}

        {error && (
          <div className="max-w-2xl mx-auto mt-8 p-4 bg-red-500/20 backdrop-blur-sm border border-red-500/30 rounded-xl text-red-400">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12 a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          </div>
        )}

        {!loading && !error && (
          <>
            {characters.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20">
                <div className="relative mb-6">
                  <div className="w-24 h-24 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-full flex items-center justify-center animate-pulse">
                    <svg className="w-12 h-12 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.3-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.3-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  </div>
                  <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center text-white text-xs font-bold animate-bounce">
                    0
                  </div>
                </div>
                <div className="text-xl font-medium text-gray-400 mb-2">暂无角色</div>
                <div className="text-sm text-gray-500">请先在剧本页面创建角色</div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {characters.map((character) => (
                  <div key={character.id} className="relative">
                    <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl blur opacity-30"></div>
                    <div className="relative bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden hover:border-white/20 transition-all duration-300 group">
                      <div className="bg-gradient-to-r from-blue-600/30 to-purple-600/30 px-6 py-4 border-b border-white/10">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-blue-500/30">
                              {character.name.charAt(0)}
                            </div>
                            <div>
                              <h3 className="font-semibold text-white">{character.name}</h3>
                              <div className="text-xs text-gray-400">角色ID: {character.id}</div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="p-4">
                        {character.description && (
                          <div className="mb-4">
                            <div className="text-xs text-gray-500 font-medium mb-1">角色描述</div>
                            <p className="text-sm text-gray-300 line-clamp-2">{character.description}</p>
                          </div>
                        )}

                        <div className="flex gap-2 mb-4">
                          {['front', 'side', 'back'].map((view) => {
                            const ref = character.references.find(r => r.view_type === view)
                            return (
                              <div key={view} className="flex-1">
                                <div className="text-xs text-gray-400 mb-1 text-center">
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
                                    <span className="text-gray-500 text-xs">暂无图片</span>
                                  )}
                                </div>
                              </div>
                            )
                          })}
                        </div>

                        <div className="bg-slate-900/50 rounded-xl p-3 mb-4 border border-white/5">
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

                        <button
                          onClick={() => handleGenerateReferences(character.id)}
                          disabled={generatingId === character.id}
                          className={`w-full py-2.5 px-4 rounded-xl font-medium transition-all ${
                            generatingId === character.id
                              ? 'bg-gray-600 cursor-not-allowed'
                              : 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 shadow-lg shadow-green-500/30 hover:-translate-y-0.5'
                          } text-white`}
                        >
                          {generatingId === character.id ? (
                            <span className="flex items-center justify-center gap-2">
                              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              生成中...
                            </span>
                          ) : (
                            <span className="flex items-center justify-center gap-2">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                              </svg>
                              生成三视图
                            </span>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
