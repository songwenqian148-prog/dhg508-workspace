/*
 * 图穷 - story data.
 *
 * Every line that comes from the Shiji is quoted from 卷086 刺客列传 and marked
 * `src` with the passage it comes from; lines marked `inv` are invented (the
 * player's own voice, or connective tissue). Branches that leave the record
 * declare `chronicle`, which asks the model to continue a history that did not
 * happen and labels it 史外 · 推演 in the interface.
 *
 * Sources are listed in research/sources.md; the evidenced / inferred / invented
 * table for every scene is in research/design.md.
 */

export const STORY = {
  start: 'a1_market',        // the route screen picks jingke/qinwang; this is the fallback
  routes: { jingke: 'a1_market', qinwang: 'q1_court' },

  // The arena decides which of these you get; declared here so the structure
  // checker can see that every one of them is reachable by play.
  battleEndings: {
    jingke: { win: 'end_assassinate', escaped: 'end_history', timeout: 'end_history' },
    qinwang: { escape: 'end_qin_escape', saved: 'end_qin_saved', caught: 'end_qin_dead' },
  },

  // ------------------------------------------------------------------ beats

  beats: {
    a1_market: {
      act: '第一幕 · 燕市',
      bg: 'yan_market',
      map: 'yan_market',
      spawn: { x: 4, y: 11, dir: 'up' },
      onEnter: 'a1_open',
      npcs: [
        { id: 'goutu', sprite: 'goutu', x: 7, y: 7, node: 'a1_goutu' },
        { id: 'gaojianli', sprite: 'gaojianli', x: 13, y: 8, node: 'a1_gao' },
        { id: 'tianguang', sprite: 'tianguang', x: 20, y: 8, node: 'a1_tianguang' },
      ],
    },

    a2_hall: {
      act: '第二幕 · 太子宫',
      bg: 'taizi_gong',
      map: 'taizi_gong',
      spawn: { x: 12, y: 12, dir: 'up' },
      onEnter: 'a2_open',
      npcs: [
        { id: 'taizidan', sprite: 'taizidan', x: 13, y: 3, node: 'a2_dan_talk' },
      ],
    },

    a3_guest: {
      act: '第三幕 · 舍人馆',
      bg: 'fanyuqi_room',
      map: 'fanyuqi_room',
      spawn: { x: 10, y: 10, dir: 'up' },
      onEnter: 'a3_open',
      npcs: [
        { id: 'fanyuqi', sprite: 'fanyuqi', x: 5, y: 4, node: 'a3_fan_talk' },
      ],
    },

    a4_prep: {
      act: '第四幕 · 备具',
      bg: 'taizi_gong',
      map: 'taizi_gong',
      spawn: { x: 12, y: 12, dir: 'up' },
      onEnter: 'a4_open',
      npcs: [
        { id: 'taizidan', sprite: 'taizidan', x: 13, y: 3, node: 'a4_dan_talk' },
        { id: 'qinwuyang', sprite: 'qinwuyang', x: 8, y: 8, node: 'a4_wuyang_chat' },
      ],
    },

    a5_yi: {
      act: '第五幕 · 易水',
      bg: 'yi_river',
      map: 'yi_river',
      spawn: { x: 6, y: 4, dir: 'right' },
      // 太子及宾客知其事者，皆白衣冠以送之 (卷086) - every actor wears white here
      tint: { color: '#efe6d4', alpha: 0.62 },
      onEnter: 'a5_open',
      npcs: [
        { id: 'taizidan', sprite: 'taizidan', x: 10, y: 3, node: 'a5_dan' },
        { id: 'gaojianli', sprite: 'gaojianli', x: 16, y: 5, node: 'a5_gao' },
        { id: 'qinwuyang', sprite: 'qinwuyang', x: 13, y: 4, node: 'a5_wuyang' },
      ],
    },

    a6_palace: {
      act: '第六幕 · 咸阳宫',
      bg: 'xianyang_hall',
      map: 'xianyang_hall',
      spawn: { x: 14, y: 11, dir: 'up' },
      onEnter: 'a6_open',
      npcs: [
        { id: 'qinwang', sprite: 'qinwang', x: 14, y: 4, node: 'a6_king_talk' },
        { id: 'qinwuyang', sprite: 'qinwuyang', x: 14, y: 15, node: 'a6_wuyang_talk' },
        { id: 'xiawuju', sprite: 'xiawuju', x: 20, y: 12, node: 'a6_doctor_talk' },
        { id: 'guard', sprite: 'guard', x: 8, y: 13, node: 'a6_guard_talk' },
      ],
    },

    // 史外: the hall after the dagger landed. Not a panel - a place you stand in,
    // with a wounded king who is still able to speak, and four ways to spend the
    // half minute before the guards reach the steps.
    a7_chaos: {
      act: '史外 · 咸阳宫',
      bg: 'xianyang_hall',
      map: 'xianyang_hall',
      spawn: { x: 14, y: 10, dir: 'up' },
      onEnter: 'a7_open',
      npcs: [
        { id: 'qinwang', sprite: 'qinwang', x: 14, y: 5, node: 'a7_king' },
        { id: 'xiawuju', sprite: 'xiawuju', x: 19, y: 12, node: 'a7_doctor' },
        { id: 'guard', sprite: 'guard', x: 9, y: 13, node: 'a7_guard' },
      ],
    },

    // ---------------------------------------------------------- 序 · 选择视角
    p0_choose: {
      act: '序 · 这一日',
      bg: 'yan_market',
      place: '燕 · 蓟城',
      onEnter: 'p0_open',
      npcs: [],
    },

    // ------------------------------------------------------ 秦 · 咸阳宫前殿
    q1_court: {
      act: '秦 · 咸阳宫',
      bg: 'xianyang_hall',
      map: 'xianyang_hall',
      spawn: { x: 14, y: 11, dir: 'up' },
      place: '咸阳宫',
      onEnter: 'q1_open',
      npcs: [
        { id: 'mengjia', sprite: 'mengjia', x: 14, y: 12, node: 'q1_mengjia' },
        { id: 'xiawuju', sprite: 'xiawuju', x: 9, y: 13, node: 'q1_doctor' },
        { id: 'guard', sprite: 'guard', x: 21, y: 13, node: 'q1_guard' },
      ],
    },

    q2_audience: {
      act: '秦 · 九宾之礼',
      bg: 'xianyang_hall',
      map: 'xianyang_hall',
      spawn: { x: 14, y: 11, dir: 'up' },
      place: '咸阳宫 · 九宾',
      onEnter: 'q2_open',
      npcs: [
        { id: 'jingke', sprite: 'jingke', x: 14, y: 12, node: 'q2_envoy' },
        { id: 'qinwuyang', sprite: 'qinwuyang', x: 12, y: 13, node: 'q2_boy' },
        { id: 'mengjia', sprite: 'mengjia', x: 18, y: 13, node: 'q2_mengjia' },
        { id: 'xiawuju', sprite: 'xiawuju', x: 9, y: 13, node: 'q2_doctor' },
      ],
    },
  },

  // ------------------------------------------------------------------ nodes

  nodes: {
    // ------------------------------------------------------- 序 · 以谁的眼睛
    p0_open: {
      lines: [
        { who: 'narrator', text: '前 227 年，冬。燕市有酒，咸阳有殿；两处都在等同一件事。' },
        { who: 'narrator', text: '你可以从其中一个人的眼睛里，过完这一天。' },
      ],
      choice: {
        prompt: '你选谁？',
        hint: '直接说出来就好，比如「我做荆轲」，或者「我当秦王」',
        options: [
          { id: 'route_jingke', label: '做荆轲：从燕市走到咸阳宫', beat: 'a1_market', effect: { flags: { route: 'jingke' } } },
          { id: 'route_qinwang', label: '做秦王：在咸阳宫等燕使上殿', beat: 'q1_court', effect: { flags: { route: 'qin' } } },
        ],
      },
    },

    // ------------------------------------------------------- 秦 · 咸阳宫（秦王线）
    q1_open: {
      lines: [
        { who: 'narrator', text: '咸阳宫。案上摊着燕国的降书，阶下站着等回话的中庶子蒙嘉。' },
        { who: 'narrator', text: '你现在是秦王政。右手还按在剑上，剑比寻常的长。' },
        { who: 'mengjia', inv: true, text: '王上，燕王恐惧，愿举国为内臣，斩樊於期之首，献督亢之图，使使以闻大王。' },
      ],
      choice: {
        npc: 'mengjia',
        prompt: '蒙嘉伏在阶下等你的话。',
        hint: '问他也行；说「让他们上殿」也行',
        options: [
          { id: 'let_in', label: '宣燕使上殿，设九宾之礼', next: 'q1_let_in' },
          { id: 'ask', label: '先追问：燕人献图，可信么', next: 'q1_ask' },
        ],
      },
    },

    q1_mengjia: {
      lines: [
        { who: 'narrator', text: '蒙嘉在阶下候着，脸上堆着恰到好处的恭敬。' },
      ],
      talk: {
        npc: 'mengjia',
        profile: '蒙嘉，秦王宠臣，中庶子。收了燕使千金之资，替燕人说话；极会揣摩上意，话总说一半。',
        scene: '咸阳宫前殿',
        perception: '秦王坐在案后，右手按剑；阶下无人；燕使的车马已在宫门外候着。',
        player_role: '秦王政',
        opening: '蒙嘉低声道：「王上，燕使已在门外。臣观其人，似非等闲。」',
        intents: [
          { id: 'let_in', desc: '命他宣燕使上殿', next: 'q1_let_in' },
          { id: 'ask', desc: '追问燕人献图的真假、燕使的来历', next: 'q1_ask' },
        ],
        fallback: '蒙嘉只是低头：「王上明鉴。」',
      },
    },

    q1_ask: {
      lines: [
        { who: 'mengjia', inv: true, text: '臣已验其图匣，封缄如制；樊将军之首，函之以漆。燕人畏王上之威，不敢有他。' },
        { who: 'narrator', text: '他说得太顺了，顺得像背过。可满殿的人都在等你点头。' },
      ],
      beat: 'q2_audience',
    },

    q1_let_in: {
      lines: [
        { who: 'narrator', text: '你点头。九宾设于庭，钟鼓齐鸣，燕使自殿门入。' },
      ],
      beat: 'q2_audience',
    },

    q1_doctor: {
      lines: [
        { who: 'xiawuju', inv: true, text: '王上今日脸色不好，臣备了药囊。' },
      ],
    },

    q1_guard: {
      lines: [
        { who: 'narrator', text: '郎中令的甲士列在阶下，按秦法，无诏不得上殿。' },
      ],
    },

    q2_open: {
      lines: [
        { who: 'narrator', text: '燕使上殿：一人捧图匣，一人捧首函。' },
        { who: 'narrator', text: '捧图匣的那个走得很稳；捧首函的那个，脸已经白了。' },
      ],
      choice: {
        npc: 'jingke',
        prompt: '燕使在阶下等你发话。',
        hint: '说「取图来」也行，先问他一句也行',
        options: [
          { id: 'take_map', label: '令他把图献上', next: 'q2_map' },
          { id: 'ask_envoy', label: '先问他：燕王还有何言', next: 'q2_ask' },
        ],
      },
    },

    q2_envoy: {
      lines: [
        { who: 'narrator', text: '捧图匣的燕使抬起头来。他并不慌。' },
      ],
      talk: {
        npc: 'jingke',
        profile: '荆轲，燕之上卿，奉太子丹之命入秦。镇定、有礼，答话极稳；图匣里藏着什么，只有他知道。',
        scene: '咸阳宫九宾之礼',
        perception: '秦王高坐在案后，阶上列着九宾；秦舞阳在你身后发抖；你手里是督亢之图。',
        player_role: '秦王政',
        opening: '荆轲再拜：「北蕃之使，得见大王，死且不朽。」',
        intents: [
          { id: 'take_map', desc: '命他献图，让他上前', next: 'q2_map' },
          { id: 'ask_envoy', desc: '问他燕王还有什么话、为何带两个使者', next: 'q2_ask' },
        ],
        fallback: '荆轲垂着眼，答得不急不缓。',
      },
    },

    q2_boy: {
      lines: [
        { who: 'narrator', text: '捧首函的少年手在抖。你多看了他一眼。' },
      ],
    },

    q2_mengjia: {
      lines: [
        { who: 'mengjia', inv: true, text: '王上，燕使年少，未曾见天子之威，故振慴。' },
      ],
    },

    q2_doctor: {
      lines: [
        { who: 'xiawuju', inv: true, text: '王上，殿上无兵，臣只有药囊。' },
      ],
    },

    q2_ask: {
      lines: [
        { who: 'jingke', inv: true, text: '燕王之言：愿举国为内臣，比诸侯之列。所献之图，督亢沃野，尽在其中。' },
        { who: 'narrator', text: '他把图匣又向前举了一寸。' },
      ],
      next: 'q2_map',
    },

    q2_map: {
      lines: [
        { who: 'narrator', text: '「取舞阳所持地图。」你说。' },
        { who: 'narrator', text: '图在案上展开，一寸一寸。图穷，匕首见。' },
        { who: 'narrator', text: '你的袖子被人抓住了——半个殿的人都在往后退，而你的剑太长，一时拔不出来。' },
      ],
      battle: 'qinwang',
    },

    // ------------------------------------------------------- 荆轲线的最后一击
    a6_battle: {
      lines: [
        { who: 'narrator', text: '图穷匕见。你左手抓住他的袖子，右手已经握住了匕首。' },
        { who: 'narrator', text: '这一回不按史书写。追上他，刺中三下。' },
      ],
      battle: 'jingke',
    },

    // ---------------------------------------------------------- 第一幕 燕市
    a1_open: {
      lines: [
        { who: 'narrator', text: '燕市。日暮，酒旗低垂，风里是腥膻与炭火气。' },
        { who: 'narrator', text: '荆轲，卫人，其先齐人，徙于卫；而之燕，燕人谓之荆卿。好读书击剑，嗜酒。', src: '卷086' },
        { who: 'narrator', text: '日与狗屠及善击筑者高渐离饮于燕市。', src: '卷086' },
        { who: 'jingke', inv: true, text: '……渐离，再击一曲。' },
      ],
      next: 'a1_memory',
    },

    a1_memory: {
      lines: [
        { who: 'narrator', text: '酒未至，你想起从前。' },
        { who: 'narrator', text: '尝游过榆次，与盖聂论剑。盖聂怒而目之。', src: '卷086' },
        { who: 'narrator', text: '又游于邯郸，鲁句践与你博，争道；鲁句践怒而叱之。', src: '卷086' },
        { who: 'narrator', text: '那时你如何应对，今日仍在你身上。' },
      ],
      choice: {
        prompt: '当年在榆次与邯郸，你是——',
        options: [
          {
            label: '嘿而逃去：不与盖聂争，不与鲁句践辩',
            effect: { stats: { sword: 0, composure: 1 }, flags: { remembered: 'ran' } },
            next: 'a1_flee_ok',
          },
          {
            label: '争道不让：与鲁句践相博，怒而叱之',
            effect: { stats: { sword: 1, composure: -1 }, flags: { remembered: 'fought' } },
            next: 'a1_fight_ok',
          },
          {
            label: '皆已忘之',
            effect: { flags: { remembered: 'none' } },
            next: 'a1_forget_ok',
          },
        ],
      },
    },

    a1_flee_ok: {
      lines: [
        { who: 'narrator', text: '盖聂曰：「固去也，吾曩者目摄之！」', src: '卷086' },
        { who: 'narrator', text: '你走得干净。剑术未必精，气却沉得住。' },
      ],
      next: 'a1_hint',
    },

    a1_fight_ok: {
      lines: [
        { who: 'narrator', text: '你争了。争道之后，鲁句践与你遂不复会。' },
        { who: 'narrator', text: '你手上多了些本事，心上也多了一层火。' },
      ],
      next: 'a1_hint',
    },

    a1_forget_ok: {
      lines: [
        { who: 'narrator', text: '忘了最好。燕市有酒，酒里有筑声。' },
      ],
      next: 'a1_hint',
    },

    a1_hint: {
      lines: [
        { who: 'narrator', text: '（走近高渐离或狗屠，按 E 交谈；与田光说话，方能入太子宫。）' },
      ],
    },
    a1_goutu: {
      // AI conversation: this character answers in their own voice.
      talk: {
        npc: 'goutu',
        profile: '狗屠，燕市上卖狗肉的。粗人，嗓门大，讲义气，嘴上不饶人心里软；知道荆轲爱喝酒，也知道他最近心事重。',
        scene: '燕市酒肆，日暮',
        perception: '荆轲坐在对面，酒喝了半酣；高渐离在旁边击筑；你的案上还摆着没剔完的肉。',
        opening: '狗屠把刀往案上一拍：「荆卿，你又在这儿坐一天。肉都凉了。」',
        intents: [
          { id: 'ask_jingke', desc: '问他看得出我有什么心事' },
          { id: 'order', desc: '再要酒要肉，说些闲话' },
        ],
        fallback: '「哼。喝你的酒吧。」他把肉片推过来，不再问了。',
      },
    },

    // Free conversation: 高渐离 answers whatever the player types, in his own
    // voice, and only a few recognised intents move the scene along.
    a1_gao: {
      lines: [
        { who: 'narrator', text: '高渐离抱筑而坐，弦上还留着上一曲的余音。' },
      ],
      talk: {
        npc: 'gaojianli',
        profile: '高渐离，燕人，善击筑。与荆轲为友，知其非庸人。沉静，少言，以乐声与人语。身在燕市酒肆，面前有酒与狗屠的案。',
        scene: '燕市酒肆，日暮',
        perception: '荆轲坐在你对面，酒已半酣；狗屠在旁剔肉；市声渐稀，远处有人在收摊。',
        opening: '渐离抬眼：「荆卿，今日的酒，比昨日苦。」',
        intents: [
          { id: 'ask_zhu', desc: '问他方才那一曲为何那样哀，或请再击一曲', next: 'a1_gao_zhu' },
          { id: 'ask_state', desc: '问他对燕国大势、秦人东来的看法', next: 'a1_gao_state' },
          { id: 'part', desc: '告辞，起身去别处（例如去找田光）', next: 'a1_hint' },
        ],
        fallback: '渐离不语，只把筑横过来，一击，声音涩而长；再一击，市声仿佛都退开了。',
      },
    },

    a1_gao_zhu: {
      lines: [
        { who: 'narrator', text: '他把筑横在膝上，指节抵着弦，慢慢压下去。' },
        { who: 'gaojianli', inv: true, text: '这曲子没有名字。燕市的人爱听快活的，可快活的曲子，我如今击不出来了。' },
        { who: 'narrator', text: '他没有再看你，只是又击了一声，很轻。' },
      ],
      next: 'a1_hint',
    },

    a1_gao_state: {
      lines: [
        { who: 'gaojianli', inv: true, text: '秦人已过易水之西。燕小，兵不足三万，太子终日与术士谋，谋的都是快的法子。' },
        { who: 'gaojianli', inv: true, text: '荆卿，快的法子，多半要一个人去死。' },
        { who: 'narrator', text: '他说完，替你把爵斟满，像什么也没说过。' },
      ],
      next: 'a1_hint',
    },

    a1_tianguang: {
      lines: [
        { who: 'narrator', text: '田光先生，燕之处士。知其非庸人也，善待之。', src: '卷086' },
        { who: 'tianguang', text: '荆卿。太子闻光壮盛之时，不知吾形已不逮也。', src: '卷086' },
        { who: 'tianguang', text: '光窃不自外，言足下于太子也。愿足下过太子于宫。', src: '卷086' },
        { who: 'jingke', text: '谨奉教。', src: '卷086' },
        { who: 'narrator', text: '田光起身，忽又停住。' },
        { who: 'tianguang', text: '太子告光曰：「所言者，国之事也，愿先生勿泄。」是太子疑光也。', src: '卷086' },
        { who: 'tianguang', text: '夫为行而使人疑之，非节侠也。愿足下急过太子，言光已死，明不言也。', src: '卷086' },
        { who: 'narrator', text: '因遂自刎而死。', src: '卷086' },
        { who: 'narrator', text: '血落在燕市的土里，很快被踩乱了。' },
      ],
      choice: {
        prompt: '田光的尸身还温着。你——',
        options: [
          {
            label: '赴太子之宫，言光已死',
            effect: { flags: { went_to_dan: true } },
            next: 'a1_depart',
          },
          {
            label: '不受其托，连夜出燕',
            ending: 'end_flee',
            chronicle: {
              divergence: '田光自刎之后，荆轲没有去太子宫，而是连夜离开了燕国。',
              context: '荆轲是卫人，游于诸侯，与燕市狗屠、高渐离为友；田光以死激之。若他不受此托，燕太子丹将另求刺客，或终于无策。',
              fallback: '那一夜之后，燕市少了一个喝酒的人。太子丹的门下又来了几个游士，都看了田光的死，又都走了。荆轲的名字，只留在高渐离的筑声里。',
            },
          },
        ],
      },
    },

    a1_depart: {
      lines: [
        { who: 'narrator', text: '你入太子宫。太子再拜而跪，膝行流涕。' },
      ],
      beat: 'a2_hall',
    },

    // ------------------------------------------------------- 第二幕 太子宫
    a2_open: {
      lines: [
        { who: 'narrator', text: '太子丹，故尝质于赵；秦王政生于赵，其少时与丹欢。及政立为秦王，而丹质于秦，秦王遇之不善，丹怨而亡归。', src: '卷086' },
        { who: 'taizidan', text: '田先生不知丹之不肖，使得至前，此天之所以哀燕而不弃其孤也。', src: '卷086' },
        { who: 'taizidan', text: '今秦有贪利之心，而欲不可足也。非尽天下之地，臣海内之王者，其意不厌。', src: '卷086' },
        { who: 'taizidan', text: '诚得劫秦王，使悉反诸侯侵地，若曹沫之与齐桓公，则大善矣；则不可，因而刺杀之。', src: '卷086' },
        { who: 'taizidan', text: '此丹之上愿，而不知所委命，唯荆卿留意焉。', src: '卷086' },
        { who: 'jingke', text: '此国之大事也，臣驽下，恐不足任使。', src: '卷086' },
        { who: 'narrator', text: '太子前顿首，固请毋让。' },
      ],
      choice: {
        npc: 'taizidan',
        perception: '太子丹跪坐在席上，身向前倾，等你开口；殿外有甲士换岗的声音。',
        prompt: '你终于开口——',
        options: [
          {
            label: '许诺：先劫秦王，不成则刺（史实）',
            effect: { flags: { plan: 'hijack' }, stats: { trust: 1 } },
            next: 'a2_fan',
          },
          {
            label: '许诺：不必生劫，直取其首',
            effect: { flags: { plan: 'kill' }, stats: { composure: -1 } },
            next: 'a2_kill_talk',
          },
          {
            label: '劝太子：燕小弱，不如西约三晋、南连齐楚',
            effect: { flags: { plan: 'advice' }, stats: { trust: -1 } },
            next: 'a2_advice',
          },
        ],
      },
    },

    a2_kill_talk: {
      lines: [
        { who: 'taizidan', inv: true, text: '……丹要的是活着的秦王，跪在坛上，还地于诸侯。' },
        { who: 'jingke', inv: true, text: '死人不会还地。但死人也不再发兵。' },
        { who: 'narrator', text: '太子沉默了很久，终于点头。殿外的风把帷幔吹起一角，像谁的手。' },
      ],
      next: 'a2_fan',
    },

    a2_advice: {
      lines: [
        { who: 'taizidan', text: '太傅鞠武亦尝言：西约三晋，南连齐楚，北购于单于。', src: '卷086' },
        { who: 'taizidan', inv: true, text: '其计旷日弥久。秦兵旦暮渡易水，丹等不得。' },
        { who: 'narrator', text: '他说完，把身子伏得更低。你知道这劝不必再劝了。' },
      ],
      chronicle: {
        divergence: '荆轲劝太子丹放弃行刺，改用合纵之策；太子丹没有接受，但也没有立刻逼他动身。',
        context: '鞠武原议：西约三晋、南连齐楚、北购单于，而后可图。太子丹以「旷日弥久」拒之。',
        fallback: '那条路太慢。慢到秦的郡县一圈圈围过来，等到三晋的使者还在路上，易水已经结了冰。',
      },
      next: 'a2_fan',
    },
    a2_dan_talk: {
      // AI conversation: this character answers in their own voice.
      talk: {
        npc: 'taizidan',
        profile: '太子丹，燕国太子，曾在秦为质，受秦王轻慢。心里憋着一口气，急，怕，又不肯承认自己怕。',
        scene: '太子宫',
        perception: '荆轲坐在席上下首；殿外有甲士换岗；案上摊着燕国的舆图。',
        opening: '太子丹往前挪了半席：「荆卿，丹这几夜总睡不安。你说，秦王真会因一卷图、一颗头，就肯见我的人？」',
        intents: [
          { id: 'reassure', desc: '宽他的心，让他安心等待' },
          { id: 'plan', desc: '与他说清入秦之后的打算', next: 'a2_open' },
        ],
        fallback: '他点点头，手还是按在舆图上没松开。',
      },
    },

    a2_fan: {
      lines: [
        { who: 'narrator', text: '秦将樊於期得罪于秦王，亡之燕，太子受而舍之。', src: '卷086' },
        { who: 'narrator', text: '荆轲知太子不忍，乃遂私见樊於期。' },
      ],
      choice: {
        prompt: '去见樊於期之前，你想的是什么？',
        options: [
          {
            label: '私见樊将军，说以首级（史实）',
            effect: { flags: { fan_seen: 'private' } },
            next: 'a2_fan_go',
          },
          {
            label: '请太子亲自取其首',
            effect: { flags: { fan_seen: 'asked_dan' } },
            next: 'a2_fan_ask',
          },
        ],
      },
    },

    a2_fan_ask: {
      lines: [
        { who: 'taizidan', inv: true, text: '樊将军穷困来归丹，丹不忍以己之私而伤长者之意。愿足下更虑之。' },
        { who: 'narrator', text: '太子不肯。天下没有第二件能让秦王开门的东西。' },
      ],
      chronicle: {
        divergence: '荆轲没有自己去劝樊於期，而是请太子丹开口索取他的首级。',
        context: '樊於期是秦国叛将，父母宗族皆为戮没，秦王购其首金千斤、邑万家。太子丹曾受而舍之。',
        fallback: '太子丹终究没有开口。那座舍人馆的门，每日照旧开着，樊於期每日照旧磨他的剑——他并不知道门外的计议，已经绕不过他的头。',
      },
      next: 'a2_fan_go',
    },

    a2_fan_go: {
      lines: [
        { who: 'narrator', text: '你入舍人馆。' },
      ],
      beat: 'a3_guest',
    },

    // ------------------------------------------------------- 第三幕 舍人馆
    a3_open: {
      lines: [
        { who: 'fanyuqi', inv: true, text: '荆卿。燕市里的酒，还够喝么？' },
        { who: 'jingke', text: '秦之遇将军，可谓深矣：父母宗族，皆为戮没。', src: '卷086' },
        { who: 'jingke', text: '今闻购将军首，金千斤，邑万家，将奈何？', src: '卷086' },
        { who: 'fanyuqi', text: '於期每念之，常痛于骨髓，顾计不知所出耳。', src: '卷086' },
      ],
      choice: {
        npc: 'fanyuqi',
        perception: '樊於期立在屋中，手按刀柄，眼睛红着；案上一盏灯，火苗不稳。',
        prompt: '你要如何说下去？',
        options: [
          {
            label: '直言：愿得将军之首以献秦王（史实）',
            effect: { flags: { fan_head: 'asked' } },
            next: 'a3_ask_head',
          },
          {
            label: '先言秦之暴，待其自决',
            effect: { flags: { fan_head: 'waited' }, stats: { composure: 1 } },
            next: 'a3_wait_head',
          },
          {
            label: '终不忍言，起身辞去',
            effect: { flags: { fan_head: 'spared' } },
            next: 'a3_spare',
          },
        ],
      },
    },

    a3_ask_head: {
      lines: [
        { who: 'jingke', text: '今有一言，可以解燕国之患，而报将军之仇者，何如？', src: '卷086' },
        { who: 'fanyuqi', text: '为之奈何？', src: '卷086' },
        { who: 'jingke', text: '愿得将军之首以献秦王，秦王必喜而见臣。臣左手把其袖，右手揕其胸；然则将军之仇报，而燕见陵之愧除矣。', src: '卷086' },
        { who: 'fanyuqi', text: '此臣之日夜切齿腐心也，乃今得闻教！', src: '卷086' },
        { who: 'narrator', text: '遂自刭。' },
        { who: 'narrator', text: '太子闻之，驰往，伏尸而哭，极哀。既已不可奈何，乃遂盛樊於期首，函封之。', src: '卷086' },
      ],
      next: 'a3_done',
    },

    a3_wait_head: {
      lines: [
        { who: 'jingke', text: '将军之仇，与燕之社稷，孰重？', src: '卷086' },
        { who: 'fanyuqi', inv: true, text: '……你是要我的头。' },
        { who: 'narrator', text: '他自己说出来了。说出来的那一瞬，他反倒松了一口气。' },
        { who: 'fanyuqi', text: '此臣之日夜切齿腐心也，乃今得闻教！', src: '卷086' },
        { who: 'narrator', text: '遂自刭。太子驰往，伏尸而哭，极哀。' },
      ],
      next: 'a3_done',
    },

    a3_spare: {
      lines: [
        { who: 'narrator', text: '你没有说出口。你起身，向他行了一礼，走出舍人馆。' },
        { who: 'narrator', text: '樊於期送到门口。他好像明白，又好像不明白。' },
      ],
      chronicle: {
        divergence: '荆轲没有向樊於期索要首级，空手离开了舍人馆。',
        context: '秦王购樊於期首金千斤、邑万家；荆轲原拟以樊於期首与督亢地图为信物入秦。没有这两件，秦王不会见他。',
        fallback: '那一颗头还长在他颈上。于是荆轲手里只剩一卷督亢地图——一卷地图换不来咸阳宫的九宾之礼，也换不来那半步的距离。',
      },
      next: 'a3_done',
    },
    a3_fan_talk: {
      // AI conversation: this character answers in their own voice.
      talk: {
        npc: 'fanyuqi',
        profile: '樊於期，秦国将军，兵败得罪秦王，父母宗族被杀，逃亡到燕，寄在太子门下。恨到骨头里，也怯。',
        scene: '舍人馆',
        perception: '荆轲站在屋中；灯很暗；你的剑横在膝上，剑鞘有裂。',
        opening: '樊於期抬头看你，眼睛里都是红丝：「荆卿，你也是来劝我的？」',
        intents: [
          { id: 'ask_hate', desc: '问他有多恨秦王、恨到什么地步' },
          { id: 'head', desc: '开口要他的头（引出献首之计）', next: 'a3_open' },
        ],
        fallback: '他低下头，手指在剑鞘的裂口上来回摸。',
      },
    },

    a3_done: {
      lines: [
        { who: 'narrator', text: '你回到太子宫。殿上摆着两样东西：一柄匕首，一卷地图。' },
      ],
      beat: 'a4_prep',
    },

    // --------------------------------------------------------- 第四幕 备具
    a4_open: {
      lines: [
        { who: 'narrator', text: '于是太子豫求天下之利匕首，得赵人徐夫人匕首，取之百金，使工以药焠之。', src: '卷086' },
        { who: 'narrator', text: '以试人，血濡缕，人无不立死者。', src: '卷086' },
        { who: 'narrator', text: '燕国有勇士秦舞阳，年十三，杀人，人不敢忤视。乃令秦舞阳为副。', src: '卷086' },
        { who: 'narrator', text: '荆轲有所待，欲与俱；其人居远未来，而为治行。', src: '卷086' },
        { who: 'taizidan', inv: true, text: '荆卿，秦兵旦暮渡易水。' },
        { who: 'taizidan', text: '日已尽矣，荆卿岂有意哉？丹请得先遣秦舞阳。', src: '卷086' },
      ],
      choice: {
        npc: 'taizidan',
        perception: '太子丹立在阶上，袖口沾了墨；阶下秦舞阳在磨刀；更漏已过三刻。',
        prompt: '太子在催。你——',
        options: [
          {
            label: '怒叱太子：往而不返者，竖子也！（史实）',
            effect: { flags: { waited: false, anger: true }, stats: { composure: -1 } },
            next: 'a4_angry',
          },
          {
            label: '固请待客至，同入秦',
            effect: { flags: { waited: true }, stats: { composure: 1 } },
            next: 'a4_wait',
          },
          {
            label: '默然受命，即日就道',
            effect: { flags: { waited: false, anger: false }, stats: { composure: 1 } },
            next: 'a4_quiet',
          },
        ],
      },
    },

    a4_angry: {
      lines: [
        { who: 'jingke', text: '何太子之遣？往而不返者，竖子也！', src: '卷086' },
        { who: 'jingke', text: '且提一匕首入不测之强秦，仆所以留者，待吾客与俱。今太子迟之，请辞决矣！', src: '卷086' },
        { who: 'narrator', text: '于是遂发。那位客人始终没有来。' },
      ],
      next: 'a4_wuyang_talk',
    },

    a4_quiet: {
      lines: [
        { who: 'jingke', inv: true, text: '……诺。' },
        { who: 'narrator', text: '你没有争。你只是把匕首的鞘又紧了一遍。那位客人没有来，你也不再等了。' },
      ],
      next: 'a4_wuyang_talk',
    },

    a4_wait: {
      lines: [
        { who: 'jingke', inv: true, text: '请待三日。客至，则二人俱入；客不至，轲独往。' },
        { who: 'narrator', text: '太子迟疑，终于应了。第三日薄暮，一辆车停在宫门外。' },
        { who: 'narrator', text: '那人自齐来，姓秦，名舞阳的乡人，剑不离手。他与你说了一夜的话。' },
      ],
      chronicle: {
        divergence: '荆轲没有在太子催促下当天出发，他等到了那位远方的客人，二人一同入秦。',
        context: '史记载：荆轲有所待，欲与俱，其人居远未来；太子丹疑其改悔，催之，荆轲怒而带着十三岁的秦舞阳出发。此处让他等到了。',
        fallback: '两个人进咸阳宫，两柄匕首，两双手。那一刻的历史还没有写。',
      },
      next: 'a4_wuyang_talk',
    },

    // A second free conversation, the night before the road: a thirteen-year-old
    // who has killed a man and has never seen a king's hall.
    a4_wuyang_talk: {
      lines: [
        { who: 'narrator', text: '秦舞阳在阶下磨刀。十三岁，杀过人，人不敢忤视。' },
      ],
      talk: {
        npc: 'qinwuyang',
        profile: '秦舞阳，燕国勇士，十三岁，曾杀人，人不敢忤视。貌壮而内怯，未曾见大国之威。父兄皆以勇名，他最怕的是被人看作不如父兄。',
        scene: '太子宫阶下，临行前夜',
        perception: '荆轲站在阶上，匕首在匣中；堂上灯很暗；明日就要向西去秦国，听说咸阳宫的阶有九级。',
        opening: '舞阳停下磨刀，抬头：「荆卿，秦王的宫，有多大？」',
        intents: [
          { id: 'teach', desc: '教他：匕首藏在图中，见图穷再动，不要看群臣', effect: { flags: { wuyang_taught: true }, stats: { composure: 1 } }, next: 'a4_wuyang_taught' },
          { id: 'reassure', desc: '安抚他，说些宽心的话', next: 'a4_wuyang_soft' },
          { id: 'leave', desc: '不再多言，令他早些睡，明日就道', next: 'a4_leave' },
        ],
        fallback: '他把刀横在膝上，眼白很亮，没有再说第二句。',
      },
    },

    a4_wuyang_taught: {
      lines: [
        { who: 'jingke', inv: true, text: '图穷则匕见。你只做一件事：把图捧稳。其余的事，我来。' },
        { who: 'narrator', text: '他点头，很用力地点了两次，然后把刀收进鞘里，手不抖了。' },
      ],
      next: 'a4_leave',
    },

    a4_wuyang_soft: {
      lines: [
        { who: 'narrator', text: '你说了些闲话：燕市的酒、狗屠的刀、易水的鱼。' },
        { who: 'qinwuyang', inv: true, text: '荆卿，我听说秦王的殿上，群臣都不许带兵器。' },
        { who: 'narrator', text: '他说这话时，是在安慰自己。' },
      ],
      next: 'a4_leave',
    },

    a4_leave: {
      lines: [
        { who: 'narrator', text: '于是发。白衣冠者送之，至于易水之上。' },
      ],
      beat: 'a5_yi',
    },

    a4_dan_talk: {
      lines: [
        { who: 'taizidan', inv: true, text: '丹已备下九宾之礼的文书，与督亢之图。' },
      ],
    },

    a4_wuyang_chat: {
      lines: [
        { who: 'qinwuyang', inv: true, text: '荆卿，你说的那座咸阳宫，大不大？' },
      ],
    },

    // ----------------------------------------------------------- 第五幕 易水
    a5_open: {
      lines: [
        { who: 'narrator', text: '太子及宾客知其事者，皆白衣冠以送之。至易水之上，既祖，取道。', src: '卷086' },
        { who: 'narrator', text: '高渐离击筑，荆轲和而歌，为变徵之声。士皆垂泪涕泣。', src: '卷086' },
      ],
      next: 'a5_song',
    },

    a5_song: {
      lines: [
        { who: 'jingke', text: '风萧萧兮易水寒，壮士一去兮不复还！', src: '卷086' },
        { who: 'narrator', text: '复为羽声慷慨，士皆瞋目，发尽上指冠。', src: '卷086' },
      ],
      choice: {
        prompt: '歌罢，你——',
        options: [
          {
            label: '就车而去，终已不顾（史实）',
            effect: { flags: { looked_back: false }, stats: { composure: 1 } },
            next: 'a5_go',
          },
          {
            label: '回望燕市的方向，与渐离对视',
            effect: { flags: { looked_back: true }, stats: { composure: -1 } },
            next: 'a5_look_back',
          },
          {
            label: '再击一曲，与众人同哭',
            effect: { flags: { looked_back: true }, stats: { composure: -1, trust: 1 } },
            next: 'a5_weep',
          },
        ],
      },
    },

    a5_look_back: {
      lines: [
        { who: 'narrator', text: '你回头。高渐离的手停在弦上，没有再击。' },
        { who: 'narrator', text: '那一瞬间，易水的声音很大，大得像有人在你耳边说不必去了。' },
      ],
      chronicle: {
        divergence: '易水送别时，荆轲回头看了高渐离一眼，没有像史书那样「终已不顾」。',
        context: '史记载荆轲就车而去，终已不顾。此处他回了头，带走了燕市的最后一眼。',
        fallback: '他回头的那一眼，被岸上的人记了很多年。后来高渐离在宋子为人佣保，夜里击筑，仍会想起那个回头的人。',
      },
      next: 'a5_go',
    },

    a5_weep: {
      lines: [
        { who: 'narrator', text: '你击筑而歌，众人和之。哭声与筑声一起，落在易水里。' },
        { who: 'narrator', text: '良久，你才登车。' },
      ],
      next: 'a5_go',
    },

    a5_go: {
      lines: [
        { who: 'narrator', text: '遂至秦。持千金之资币物，厚遗秦王宠臣中庶子蒙嘉。', src: '卷086' },
        { who: 'narrator', text: '秦王闻之，大喜，乃朝服，设九宾，见燕使者咸阳宫。', src: '卷086' },
      ],
      beat: 'a6_palace',
    },

    a5_dan: {
      lines: [
        { who: 'taizidan', inv: true, text: '丹在蓟城等你的消息。若事不成……燕就只剩易水了。' },
      ],
    },
    a5_gao: {
      // AI conversation: this character answers in their own voice.
      talk: {
        npc: 'gaojianli',
        profile: '高渐离，燕人，善击筑。荆轲的酒友，也是唯一真正懂他的人。知道这一去不回，却什么也不劝。',
        scene: '易水边，送别',
        perception: '荆轲穿着白衣，站在车旁；岸上的人都低着头；你的筑抱在怀里，弦已经调好了。',
        opening: '高渐离把筑抱紧了些：「荆卿。这一段，我替你击。你要说什么，我跟着。」',
        intents: [
          { id: 'ask_song', desc: '请他击一曲送行' },
          { id: 'farewell', desc: '与他说几句告别的话', next: 'a5_song' },
        ],
        fallback: '他没再问，手指落在弦上。',
      },
    },

    a5_wuyang: {
      lines: [
        { who: 'qinwuyang', inv: true, text: '图在我手里。图穷之时，匕首就会出来，对么？' },
      ],
    },

    // ------------------------------------------------------- 第六幕 咸阳宫
    a6_open: {
      lines: [
        { who: 'narrator', text: '咸阳宫。九宾设于庭，秦王的冠在阶上，黑得发亮。' },
        { who: 'narrator', text: '荆轲奉樊於期头函，而秦舞阳奉地图柙，以次进。', src: '卷086' },
        { who: 'narrator', text: '至陛，秦舞阳色变振恐，群臣怪之。', src: '卷086' },
        { who: 'jingke', text: '北蕃蛮夷之鄙人，未尝见天子，故振慴。愿大王少假借之，使得毕使于前。', src: '卷086' },
        { who: 'qinwang', text: '取舞阳所持地图。', src: '卷086' },
        { who: 'narrator', text: '轲既取图奏之。秦王发图。' },
        { who: 'narrator', text: '图穷而匕首见。', src: '卷086' },
      ],
      choice: {
        prompt: '匕首在手。距离是半步。',
        options: [
          {
            label: '左手把其袖，右手揕其胸（史实）',
            effect: { flags: { strike: 'sleeve' } },
            next: 'a6_sleeve',
          },
          {
            label: '先断其剑，再取其命',
            effect: { flags: { strike: 'sword' } },
            next: 'a6_sword',
          },
          {
            label: '厉声数秦之罪，欲生劫之',
            effect: { flags: { strike: 'speech', hijack: true } },
            next: 'a6_speech',
          },
        ],
      },
    },

    a6_sleeve: {
      lines: [
        { who: 'narrator', text: '你左手把其袖，右手持匕首揕之。' },
        { who: 'narrator', text: '未至身，秦王惊，自引而起，袖绝。', src: '卷086' },
        { who: 'narrator', text: '拔剑。剑长，操其室。时惶急，剑坚，故不可立拔。', src: '卷086' },
        { who: 'narrator', text: '荆轲逐秦王，秦王环柱而走。', src: '卷086' },
      ],
      next: 'a6_battle',
    },

    a6_sword: {
      lines: [
        { who: 'narrator', text: '你不去抓那截袖子。你先去夺他的剑。' },
        { who: 'narrator', text: '秦法，群臣侍殿上者不得持尺寸之兵；他的剑，是这殿上唯一能杀你的铁。' },
        { who: 'narrator', text: '剑从鞘里出来了一半，你的匕首已经到了。' },
      ],
      chronicle: {
        divergence: '图穷匕见的一刻，荆轲没有去抓秦王的袖子，而是先夺他腰间那把拔不出的长剑。',
        context: '史载：荆轲左手把秦王之袖，右手揕之；未至身，秦王惊，自引而起，袖绝。秦王拔剑，剑长，操其室，惶急剑坚不可立拔。秦法：殿上群臣不得持尺寸之兵。',
        outcome: '荆轲夺剑得手：剑连着鞘被钉在柱上，秦王右手受伤，退到九宾之后；郎中尚未上殿，群臣徒手不敢前。荆轲没有立刻杀死秦王——他要的是「约契」，这给了秦廷喘息。',
        fallback: '那把剑比史书里的更早出鞘了一线。剩下的事情，取决于这一线。',
      },
      next: 'a6_battle',
    },

    // The one place where earlier choices decide the outcome: whether the extra
    // man was waited for, or whether the sword hand was trained in Yuci.
    a6_sword_check: {
      route: {
        any: [{ flag: 'waited', value: true }, { stat: { name: 'sword', gte: 1 } }],
        then: 'a6_sword_hit',
        else: 'a6_sword_miss',
      },
    },

    a6_sword_hit: {
      lines: [
        { who: 'narrator', text: '你的匕首先到。剑连着鞘，连同拔剑的那只手，一起被你钉在柱上。' },
        { who: 'narrator', text: '殿上静了一瞬。然后群臣的袍袖、郎中的长戟、夏无且的药囊，全都涌上来。' },
        { who: 'narrator', text: '你只有一个人，一只手，和半步的距离。你已经把那半步走完了。' },
      ],
      // Not a panel: the divergence is played. You are inside the hall, the king
      // is wounded and awake, and what happens next is yours to decide by hand.
      beat: 'a7_chaos',
    },

    a6_sword_miss: {
      lines: [
        { who: 'narrator', text: '剑柄从你指缝里滑了出去——不是快，是那半步太远。' },
        { who: 'narrator', text: '秦王一惊，剑脱手，人却退开了。左右已经喊了出来：「王负剑！」' },
      ],
      next: 'a6_wound',
    },

    a6_speech: {
      lines: [
        { who: 'jingke', inv: true, text: '秦王！燕人今日不取汝头，只求汝一言：还诸侯之侵地！' },
        { who: 'narrator', text: '满殿都静了。史书上写，他本欲生劫之，必得约契以报太子。', src: '卷086' },
        { who: 'narrator', text: '秦王不应。他绕柱而走。', src: '卷086' },
      ],
      next: 'a6_battle',
    },

    a6_chase: {
      lines: [
        { who: 'narrator', text: '群臣皆愕，卒起不意，尽失其度。', src: '卷086' },
        { who: 'narrator', text: '诸郎中执兵皆陈殿下，非有诏召不得上。以故荆轲乃逐秦王。', src: '卷086' },
        { who: 'narrator', text: '而卒惶急，无以击轲，以手共搏之。', src: '卷086' },
        { who: 'narrator', text: '是时，侍医夏无且以其所奉药囊提荆轲。', src: '卷086' },
      ],
      choice: {
        prompt: '药囊砸在你肩上。秦王绕柱，剑还在鞘里。',
        options: [
          {
            label: '舍王而逐剑：先斩夏无且，再取秦王',
            effect: { flags: { chase: 'doctor' } },
            next: 'a6_doctor',
          },
          {
            label: '紧追秦王，不给他拔剑的工夫',
            effect: { flags: { chase: 'king' } },
            next: 'a6_king',
          },
          {
            label: '掷匕首，取其一击',
            effect: { flags: { chase: 'throw' } },
            next: 'a6_throw',
          },
        ],
      },
    },

    a6_doctor: {
      lines: [
        { who: 'narrator', text: '你回身，匕首划开药囊，药末扑了满殿。夏无且跌坐在阶上。' },
        { who: 'narrator', text: '这一回身的工夫，左右已经喊了出来——' },
        { who: 'guard', text: '王负剑！', src: '卷086' },
      ],
      next: 'a6_wound',
    },

    a6_king: {
      lines: [
        { who: 'narrator', text: '你贴着他追，绕着那根朱漆的柱子。他的袖子还在你手里，只有一截。' },
        { who: 'narrator', text: '秦王方环柱走，卒惶急，不知所为。左右乃曰：「王负剑！」', src: '卷086' },
      ],
      next: 'a6_wound',
    },

    a6_throw: {
      lines: [
        { who: 'narrator', text: '你退半步，把匕首掷了出去。' },
      ],
      next: 'a6_miss',
    },

    a6_wound: {
      lines: [
        { who: 'narrator', text: '负剑，遂拔，以击荆轲，断其左股。', src: '卷086' },
        { who: 'narrator', text: '你倒了。血在黑色的殿砖上，很快看不出颜色。' },
      ],
      next: 'a6_last',
    },

    a6_miss: {
      lines: [
        { who: 'narrator', text: '匕首擦着他的肩过去，钉进铜柱，颤了几颤。' },
        { who: 'narrator', text: '秦王复击轲，轲被八创。', src: '卷086' },
      ],
      next: 'a6_last',
    },

    a6_last: {
      lines: [
        { who: 'narrator', text: '轲自知事不就，倚柱而笑，箕踞以骂。', src: '卷086' },
        { who: 'jingke', text: '事所以不成者，以欲生劫之，必得约契以报太子也。', src: '卷086' },
        { who: 'narrator', text: '于是左右既前杀轲。秦王不怡者良久。', src: '卷086' },
      ],
      next: 'a6_outcome',
    },

    a6_outcome: {
      choice: {
        prompt: '你的手还记得那半步的距离。',
        options: [
          {
            label: '就此认命：史书到此为止',
            ending: 'end_history',
          },
          {
            label: '若当日在燕市多留三日，若匕首再进半寸——',
            ending: 'end_counterfactual',
            chronicle: {
              divergence: '荆轲死在咸阳宫的柱子下面。但假如那一击刺中了呢？',
              context: '史载：荆轲把袖，袖绝；秦王拔剑不出，环柱而走；夏无且以药囊提轲；左右呼「王负剑」，遂拔剑断其左股，轲被八创。请续写一个「刺中之后」的历史：秦廷的混乱、六国的反应、燕国的处境，以及它为何仍然可能失败。不要写成胜利颂歌。',
              fallback: '如果那一刀进去了，咸阳宫会先乱三日。三日里，赵国旧地会有人起兵，燕国的使者还在路上。但秦的郡县不会因为一个死人而消失；函谷关以东，还有几十万人在等着被编入户籍。历史未必会掉头，它只是会拐一个很小的弯。',
            },
          },
        ],
      },
    },
    a6_king_talk: {
      // AI conversation: this character answers in their own voice.
      talk: {
        npc: 'qinwang',
        profile: '秦王政，此刻坐在九宾之后。刚戾自用，但此刻正看着燕使一步步上殿，心里并不轻松。',
        scene: '咸阳宫，受图之前',
        perception: '燕使在阶下；殿上不许携兵；你的剑很长，挂在腰间。',
        opening: '秦王没有看你，只问左右：「燕使到了？」',
        intents: [
          { id: 'summon', desc: '命燕使上前献图', next: 'a6_open' },
          { id: 'watch', desc: '先不动声色，看他怎么走上来' },
        ],
        fallback: '他没有再说话，指节在案上轻轻敲了一下。',
      },
    },

    a6_wuyang_talk: {
      lines: [
        { who: 'narrator', text: '秦舞阳伏在阶下，色变振恐，手里的图柙抖得响。' },
      ],
    },
    a6_doctor_talk: {
      // AI conversation: this character answers in their own voice.
      talk: {
        npc: 'xiawuju',
        profile: '夏无且，秦王侍医。谨慎、胆小，只会看病，手里只有一个药囊。',
        scene: '咸阳宫',
        perception: '秦王在阶上；燕使刚上殿；你抱着药囊站在阶侧。',
        opening: '夏无且压低声：「壮士……不，燕使。殿上不许带兵，你的图匣，可沉？」',
        intents: [
          { id: 'calm', desc: '随口敷衍他，让他别多问' },
          { id: 'ask', desc: '问他殿上的规矩、郎中有多少' },
        ],
        fallback: '他讪讪地退了半步，把药囊抱得更紧。',
      },
    },
    a6_guard_talk: {
      // AI conversation: this character answers in their own voice.
      talk: {
        npc: 'guard',
        profile: '秦王殿上的郎中，按秦法无诏不得上殿。训练有素，也怕担责任。',
        scene: '咸阳宫阶下',
        perception: '燕使在你面前经过；殿上秦王已经坐定；你的长戟拄在地上。',
        opening: '郎中低声提醒：「按秦法，无诏不得上殿。你若要进，还得等王上开口。」',
        intents: [
          { id: 'ask_law', desc: '问殿上的规矩、若是出事怎么办' },
          { id: 'pass', desc: '不再多问，只管站好' },
        ],
        fallback: '他把戟往里收了收，不再说话。',
      },
    },

    // ------------------------------------------------- 史外 · 咸阳宫（可玩）
    a7_open: {
      lines: [
        { who: 'narrator', text: '剑连同拔剑的那只手，钉在朱漆柱上。血顺着柱子往下走，滴在黑色的砖上。' },
        { who: 'narrator', text: '秦王没有倒。他倚着柱，冠歪了，一只袖子空着，眼睛却还睁着。' },
        { who: 'narrator', text: '殿下的郎中正在上阶。你有半刻，最多一刻。' },
      ],
      choice: {
        npc: 'qinwang',
        counterfactual: true,
        perception: '秦王倚柱而立，右手被剑钉住，脸色白，呼吸很重，仍在看你；阶下甲叶响成一片。',
        prompt: '你可以做一件事，也可以先跟他说话。',
        options: [
          {
            id: 'treaty',
            label: '把剑横在他颈上，逼他署约、尽反诸侯侵地',
            chronicle: {
              divergence: '荆轲在咸阳宫制住了秦王，逼他当场署约，退还诸侯被侵之地。',
              context: '史载荆轲本欲生劫秦王，「必得约契以报太子」。此分支让这个「生劫」真的成立了。',
              outcome: '秦王被制，当场应允署约；群臣不敢前；但秦的郡县、军队与文书系统仍在，一份被刀逼出来的盟约要如何发出函谷关，是接下来的问题。',
              fallback: '盟约写了，盖了印。印是真的，刀是真的。函谷关以东的郡守没有一个知道这件事，他们只按旧令征粮。',
            },
            ending: 'end_cf_treaty',
          },
          {
            id: 'kill',
            label: '不再说话，补一剑',
            chronicle: {
              divergence: '荆轲没有留秦王活口，当场杀死了他。',
              context: '史载荆轲欲生劫之，故未即杀；此处他选择了杀。',
              outcome: '秦王死于咸阳宫；秦国无太子之名分已定，公子与宗室、李斯与王翦军、以及在外的大将，会立刻开始争夺「秦王」这三个字。',
              fallback: '咸阳宫的门关了三天。三天后，一封以秦王名义发出的诏书出了函谷关，字迹与从前一般无二。',
            },
            ending: 'end_cf_kingdead',
          },
          {
            id: 'escape',
            label: '舍下秦王，趁乱夺门而出',
            chronicle: {
              divergence: '荆轲在刺伤秦王之后没有恋战，趁群臣失措逃出了咸阳宫。',
              context: '史载荆轲逐秦王，环柱而走，被夏无且药囊所阻、为左右所杀。此分支让他走了。',
              outcome: '荆轲出宫，秦闭城门大索；燕使的车马还在馆舍。秦王伤重但未死，秦廷会先封锁消息，再追。',
              fallback: '他出城的那一夜，咸阳的四门都点了火。第二天，市上一切照旧，只是买不到出关的符传了。',
            },
            ending: 'end_cf_escape',
          },
          {
            id: 'hear',
            label: '先不杀，听他要说什么',
            next: 'a7_king',
          },
        ],
      },
    },

    a7_king: {
      lines: [
        { who: 'narrator', text: '秦王倚着柱，血把黑袖浸成更深的黑。他开口时声音很稳。' },
      ],
      talk: {
        npc: 'qinwang',
        profile: '秦王政，此刻被荆轲制住、右手重伤。刚戾自用，极善以言辞争势；他知道只要拖延，阶下的郎中就会上来。他不求饶，但会试图谈条件、分化、许诺，也会试探荆轲想要什么。',
        scene: '咸阳宫，九宾之后，血未干',
        perception: '荆轲持剑立在面前，离你三步；你的右手被钉在柱上；群臣伏在殿角不敢动；阶下有甲叶声，越来越近。',
        player_role: '荆轲，燕之上卿，持剑者',
        opening: '秦王喘了一口气，笑了一下：「燕人，你要什么？」',
        intents: [
          { id: 'treaty', desc: '要他署约、退还诸侯侵地，以此换命', next: 'a7_treaty_now' },
          { id: 'kill', desc: '不再谈，动手杀他', next: 'a7_kill_now' },
          { id: 'ask_why', desc: '问他为何要灭六国、为何待燕太子不善', next: null },
          { id: 'ask_who', desc: '问他阶下的郎中还有多久上来、是否怕死', next: null },
        ],
        fallback: '他盯着你，不再说话，只把呼吸放慢，像是在等什么。',
      },
    },

    a7_treaty_now: {
      lines: [
        { who: 'narrator', text: '你说出条件。他听得很仔细，甚至点了点头。' },
        { who: 'qinwang', inv: true, text: '可以。取简来。诸侯之地，尽还。' },
        { who: 'narrator', text: '他说得太快，快得像早想好了。' },
      ],
      chronicle: {
        divergence: '荆轲在咸阳宫制住秦王，逼他当场署约退还诸侯之地。',
        context: '史载荆轲欲生劫秦王，必得约契以报太子，未成。此分支成立。',
        outcome: '秦王应允署约，群臣不敢前；但秦的郡县、军队、文书系统仍在，一纸被刀逼出的盟约要如何发出函谷关，是接下来的问题。',
        fallback: '盟约写了，盖了印。印是真的，刀是真的。函谷关以东的郡守没有一个知道这件事，他们只按旧令征粮。',
      },
      ending: 'end_cf_treaty',
    },

    a7_kill_now: {
      lines: [
        { who: 'narrator', text: '你没有再听他说完。' },
        { who: 'qinwang', inv: true, text: '……燕人，你可知你杀的不是我一人。' },
      ],
      chronicle: {
        divergence: '荆轲没有留秦王活口，在咸阳宫中当场杀死了他。',
        context: '史载荆轲本欲生劫之，故未即杀；此处他选择了杀。',
        outcome: '秦王死于咸阳宫；宗室、公子、李斯与在外的大将立刻开始争夺「秦王」这三个字；秦不会因此停下，只会更快地立一个新王。',
        fallback: '咸阳宫的门关了三天。三天后，一封以秦王名义发出的诏书出了函谷关，字迹与从前一般无二。',
      },
      ending: 'end_cf_kingdead',
    },

    a7_doctor: {
      lines: [
        { who: 'xiawuju', inv: true, text: '荆卿……不，壮士。药囊在这里，血止不住。你若要他活，让我过去。' },
      ],
    },

    a7_guard: {
      lines: [
        { who: 'narrator', text: '郎中令的甲士在阶下列成两排，没有诏，谁也不敢先上。' },
        { who: 'guard', inv: true, text: '王上！——放箭么？' },
      ],
    },
  },

  // ---------------------------------------------------------------- endings

  endings: {
    end_history: {
      tag: '史实',
      history: true,
      title: '壮士一去兮不复还',
      art: 'yi_river',
      paragraphs: [
        '秦王大怒，益发兵诣赵，诏王翦军以伐燕。十月而拔蓟城。燕王喜、太子丹等尽率其精兵东保于辽东。',
        '代王嘉遗燕王喜书曰：秦所以尤追燕急者，以太子丹故也。今王诚杀丹献之秦王，秦王必解。其后李信追丹，丹匿衍水中，燕王乃使使斩太子丹，欲献之秦。秦复进兵攻之。后五年，秦卒灭燕，虏燕王喜。',
        '其明年，秦并天下，立号为皇帝。秦逐太子丹、荆轲之客，皆亡。高渐离变名姓为人佣保，匿作于宋子。后以铅置筑中，举筑扑秦皇帝，不中，遂诛。',
        '鲁句践已闻荆轲之刺秦王，私曰：「嗟乎，惜哉其不讲于刺剑之术也！甚矣吾不知人也！曩者吾叱之，彼乃以我为非人也！」',
      ],
    },

    end_counterfactual: {
      tag: '史外 · 推演',
      history: false,
      title: '未写的那一夜',
      art: 'pillar_chase',
      paragraphs: [
        '史书只写了一次咸阳宫。那一次，匕首差了一线。',
        '你把那一线放回原处：也许是在燕市多留的三日，也许是易水边没有回的那一次头，也许是掷出去的匕首偏了半寸。',
        '下面这一段，是模型替你续的：一个没有发生过的、却并非不可能的结局。它不是史料。它存在的意义，是让你看清那半步到底有多重。',
      ],
    },

    end_flee: {
      tag: '史外 · 推演',
      history: false,
      title: '燕市之外',
      art: 'yan_market',
      paragraphs: [
        '田光死了。你没有去太子宫。',
        '你从燕市走了，像从前从榆次、从邯郸走掉那样。你身上没有匕首，只有酒气和剑。',
      ],
    },

    // ------------------------------------------- 三条史外结局（在 a7 里走出来的）
    end_cf_treaty: {
      tag: '史外 · 推演',
      history: false,
      title: '一纸盟约',
      paragraphs: [
        '秦王署了约。诸侯侵地，尽还。竹简上的字是秦的小篆，印是秦的玺。',
        '你把那卷简带出了咸阳宫。它比匕首重，也比匕首轻：重到足以让燕太子丹在蓟城哭出声，轻到出了函谷关就没有一个郡守肯认。',
        '秦没有退回河东。它只是换了一个说法：这卷简是「燕人刃王上所立」，非王本意。三个月后，王翦的军依旧在漳水边上。',
        '你活了下来，也没有活成英雄。史书里没有你这一节；史书里只写「轲被八创」。',
      ],
    },

    end_cf_kingdead: {
      tag: '史外 · 推演',
      history: false,
      title: '王者之死',
      paragraphs: [
        '秦王死在咸阳宫。这是自三家分晋以来，最大的一件事，也是最快被按住的一件事。',
        '秦不发丧。三日之后，一封以秦王名义发出的诏书照旧出了函谷关，调兵、征粮、迁民，一个字都不差。',
        '公子与宗室争立，李斯居中调度，王翦的军不动。秦没有乱，它只是更紧地攥住了「秦王」这三个字。',
        '你死了。你不知道：你杀的那个人，后来被称作始皇帝——而有没有你这一刀，他都会被称为始皇帝。',
      ],
    },

    end_cf_escape: {
      tag: '史外 · 推演',
      history: false,
      title: '出关',
      paragraphs: [
        '你出了咸阳宫，也出了咸阳城。四门点火的那一夜，你在一辆运炭的车上过的渭水。',
        '秦王伤重未死。秦先封锁消息，再封关，再追。燕使的车马还在馆舍，秦国只当是「燕人失礼，使者逃」。',
        '一个月后，你回到蓟城。太子丹没有见你，只让人送来一句话：「事不成，卿何归？」',
        '你回到了燕市。狗屠换了新刀，高渐离的筑上落了灰。你在市上又喝了一年酒，直到王翦破蓟。',
      ],
    },

    // --------------------------------------------------- 战斗结局（由打斗决定）
    end_assassinate: {
      tag: '史外 · 你打的这一场',
      history: false,
      title: '三刺',
      paragraphs: [
        '你追上去了。三下，都落在实处。秦王的冠掉在阶上，血从袖口里流出来，比史书里写的那一次多得多。',
        '殿上没有郎中敢上，因为秦法不许他们带兵上殿；夏无且的药囊扔过来了，没有砸中。',
        '这一刻之后的事，史书没有写。你只知道：那一刀到底有多重，是你自己用手量出来的。',
      ],
    },

    end_qin_escape: {
      tag: '史外 · 你打的这一场',
      history: false,
      title: '王走',
      paragraphs: [
        '你逃到了殿门。门外的郎中将戟放低，让出一条路来。',
        '身后荆轲还在追，被两个郎中拦住了。你回头看了一眼：那个人还站着，匕首还在手里。',
        '你活过了这一天。史书上是这么写的；这一回，你是自己跑出来的。',
      ],
    },

    end_qin_saved: {
      tag: '史外 · 你打的这一场',
      history: false,
      title: '郎中上殿',
      paragraphs: [
        '你没有被追上。拖到郎中们上殿，事情就不再是你的了。',
        '荆轲被按在柱上，嘴里还在骂。你想听清他在骂什么，殿上太吵了。',
        '你活着，他也还活着——但那是另一段历史了。',
      ],
    },

    end_qin_dead: {
      tag: '史外 · 你打的这一场',
      history: false,
      title: '王卒',
      paragraphs: [
        '荆轲追上了你。三下，都扎在实处。',
        '你倒在自己的殿上。冠滚下阶，群臣在远处看着，没有一个人上前。',
        '史书里没有这一节。你死在这里，秦的郡县还在，只是「秦王」这三个字，要换一个人来念了。',
      ],
    },
  },
};

