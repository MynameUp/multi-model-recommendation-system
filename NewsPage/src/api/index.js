import request from '@/utils/request'

export function login(userid, password){
  let data = {
    userid: userid,
    password: password,
  }
  // console.log(data)
  let req = request.post('api/user/login/', data)
  return req
}

export function getTourists(){
  let req = request.get('api/user/tourists/')
  return req
}

export function register(userid, password, username,  words, gender){
  let data = {
    userid: userid,
    password: password,
    tags: words,
    gender: gender,
    username: username,
  }
  console.log(data)
  let req = request.post('api/user/regis/', data)
  return req
}

export function getPicture(){
  let res = request.get('api/news/pict/')
  return res
}

export function getNewsDetail(newsid,userid){
  let res = request.get('api/news/id/?newsid='+newsid+'&userid='+userid)
  return res
}

export function getAllNewsDetail(){
  let res = request.get('api/news/all/')
  return res
}

export function getTypeNewsDetail(type){
  let res = request.get('api/news/typ/?type='+type)
  return res
}

// 修改后：直接返回 request，让 Promise 继续传递
export function updateHistory(userid, newsid) {
  return request.get(`api/news/his/?userid=${userid}&newsid=${newsid}`);
}

export function getUserHistory(userid){
  let res = request.get('api/user/his/?userid='+userid)
  return res
}

export function getRecNewsDetail(userid){
  let res = request.get('api/user/rec/?userid='+userid)
  return res
}

export function getSimilarnews(newsid){
  let res = request.get('api/news/recbs/?newsid='+newsid)
  return res
}

export function getHotNews(){
  let res = request.get('api/news/nhr/')
  return res
}

export function getComments(newsid){
  let res = request.get('api/news/com/?newsid='+newsid)
  return res
}

export function getUserdetail(newsid){
  let res = request.get('api/user/det/?userid='+newsid)
  return res
}

export function updateUser(userid, username, gender){
  let data = {
    'userid': userid,
    'username': username,
    'gender': gender,
  }
  let res = request.post('api/user/upb/', data)
  return res
}

export function updateTags(userid, tags){
  let data = {
    'userid': userid,
    'tags': tags
  }
  let res = request.post('api/user/uptags/',data)
  return res
}
export function getHotSpot(){
  let res = request.get('api/news/hotnews/')
  return res
}
export function submitComments(userid, newsid, comments){
  let data = {
    'userid': userid,
    'newsid':newsid,
    'comment': comments,
  }
  let res = request.post('api/news/subcom/',data)
  return res
}
export function submitCommentsToUser(userid, newsid, comments, touserid){
  let data = {
    'userid': userid,
    'newsid':newsid,
    'comment': comments,
    'touserid': touserid,
  }
  let res = request.post('api/news/subcomtou/',data)
  return res
}
export function updateGiveLike(userid, newsid, like){
  let res = request.get('api/news/updgivelike/?userid='+userid+'&newsid='+newsid+'&like='+like)
  return res
}
export function getMessage(userid){
  let res = request.get('api/user/message/?userid='+userid)
  return res
}
export function getTip(userid){
  let res = request.get('api/user/gettip/?userid='+userid)
  return res
}
export function setHadRead(id){
  let res = request.get('api/user/sethadread/?id='+id)
  return res
}
export function getTags(){
  let res = request.get('api/user/getRegistrPageData/')
  return res
}
export function updateRec(newsid, userid){
  let res = request.get('api/news/updateRec/?newsid='+newsid+'&userid='+userid)
  return res
}
export function updateUserHeadportrait(userid, picurl){
  let data = {
    userid: userid,
    picurl: picurl,
  }
  let res = request.post('api/user/updateheadpic/', data)
  return res
}
export function intelligentRecommend(userInput, userid, topN = 20) {
  let res = request.get('api/intelligent/recommend/', {
    params: {
      user_input: userInput,
      userid: userid,
      top_n: topN
    }
  })
  return res
}
export function uploadAvatarFile(formData) {
  // 注意：不要手动设置 Content-Type
  // axios 会自动为 FormData 设置正确的 Content-Type 和 boundary
  return request.post('api/user/updateheadpic/', formData)
}

// ========== DeepSeek 推荐智能体 API ==========

/**
 * 混合流水线推荐 (Intent→Recall→Rank→Explain)
 * @param {number|string} userid - 用户ID
 * @param {string} userQuery - 用户自然语言输入
 * @param {number} topK - 返回数量 (默认20)
 */
export function deepseekHybridRecommend(userid, userQuery, topK = 20) {
  return request.post('api/agent/deepseek/hybrid/', {
    userid: userid,
    user_query: userQuery,
    top_k: topK,
  })
}

/**
 * 混合流水线推荐 — SSE 流式版本 (打字机效果)
 *
 * 使用 fetch + ReadableStream 逐行解析后端 StreamingHttpResponse。
 * 每行是一个 JSON 对象:
 *   {"type":"phase1","intent":{...},"recommendations":[...],...}
 *   {"type":"text","content":"chunk..."}
 *   {"type":"done","total":N}
 *
 * @param {number|string} userid - 用户ID
 * @param {string} userQuery - 用户自然语言输入
 * @param {number} topK - 返回数量
 * @param {object} callbacks - 回调函数集合
 * @param {function} callbacks.onPhase1 - 收到结构化数据时调用
 * @param {function} callbacks.onText - 收到文本块时调用
 * @param {function} callbacks.onDone - 流结束时调用
 * @param {function} callbacks.onError - 出错时调用
 * @returns {AbortController} 用于取消请求
 */
export function deepseekHybridRecommendStream(userid, userQuery, topK, callbacks) {
  const controller = new AbortController();
  const baseURL = window.location.origin;

  fetch(`${baseURL}/api/agent/deepseek/hybrid/stream/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      userid: String(userid),
      user_query: userQuery,
      top_k: topK || 20,
    }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const errText = await response.text();
        callbacks.onError(new Error(`HTTP ${response.status}: ${errText}`));
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      try {
        let isDone = false;
        while (!isDone) {
          const { done, value } = await reader.read();
          isDone = done;
          if (isDone) break;

          buffer += decoder.decode(value, { stream: true });
          // 按行分割 JSON
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';  // 保留不完整的最后一行

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;

            try {
              const msg = JSON.parse(trimmed);
              switch (msg.type) {
                case 'start':
                  callbacks.onStart && callbacks.onStart(msg);
                  break;
                case 'status':
                  callbacks.onStatus && callbacks.onStatus(msg);
                  break;
                case 'phase1':
                  callbacks.onPhase1(msg);
                  break;
                case 'text':
                  callbacks.onText(msg.content);
                  break;
                case 'done':
                  callbacks.onDone(msg);
                  break;
              }
            } catch (parseErr) {
              // 非 JSON 行 (如空行/注释), 静默跳过
            }
          }
        }
        // 处理缓冲区残留
        if (buffer.trim()) {
          try {
            const msg = JSON.parse(buffer.trim());
            if (msg.type === 'done') callbacks.onDone(msg);
          } catch (e) { /* ignore */ }
        }
      } catch (streamErr) {
        if (streamErr.name !== 'AbortError') {
          callbacks.onError(streamErr);
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        callbacks.onError(err);
      }
    });

  return controller;
}

/**
 * 一键清空对话记忆
 * @param {number|string} userid - 用户ID
 */
export function clearDeepseekMemory(userid) {
  return request.post('api/agent/deepseek/clear/', {
    userid: userid,
  })
}


