require('dotenv').config();
const axios = require('axios');
const { ethers } = require('ethers');
const crypto = require('crypto');
const UserAgent = require('user-agents');
const readline = require('readline').createInterface({
  input: process.stdin,
  output: process.stdout
});
const fs = require('fs').promises;

const colors = {
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  white: '\x1b[37m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

const logger = {
  info: (msg) => console.log(`${colors.green}[✓] ${msg}${colors.reset}`),
  wallet: (msg) => console.log(`${colors.yellow}[➤] ${msg}${colors.reset}`),
  error: (msg) => console.log(`${colors.red}[✗] ${msg}${colors.reset}`),
  success: (msg) => console.log(`${colors.green}[] ${msg}${colors.reset}`),
  loading: (msg) => console.log(`${colors.cyan}[⟳] ${msg}${colors.reset}`),
  step: (msg) => console.log(`${colors.white}[➤] ${msg}${colors.reset}`),
  banner: () => {
    console.log(`${colors.cyan}${colors.bold}`);
    console.log('---------------------------------------------');
    console.log('     KiteAI Auto Bot - YetiDAO (V1.5)');
    console.log(`---------------------------------------------${colors.reset}\n`);
  },
  agent: (msg) => console.log(`${colors.white}${msg}${colors.reset}`)
};

const agents = [
  { name: 'Professor', service_id: 'deployment_KiMLvUiTydioiHm7PWZ12zJU' },
  { name: 'Crypto Buddy', service_id: 'deployment_ByVHjMD6eDb9AdekRIbyuz14' },
  { name: 'Sherlock', service_id: 'deployment_OX7sn2D0WvxGUGK8CTqsU5VJ' }
];

const loadPrompts = async () => {
  try {
    const content = await fs.readFile('prompt.txt', 'utf8');
    const lines = content.split('\n').map(line => line.trim());
    const promptGenerators = {};
    let currentAgent = null;

    for (const line of lines) {
      if (line.startsWith('[') && line.endsWith(']')) {
        currentAgent = line.slice(1, -1).trim();
        promptGenerators[currentAgent] = [];
      } else if (line && !line.startsWith('#') && currentAgent) {
        promptGenerators[currentAgent].push(line);
      }
    }

    for (const agent of agents) {
      if (!promptGenerators[agent.name] || promptGenerators[agent.name].length === 0) {
        logger.error(`No prompts found for agent ${agent.name} in prompt.txt`);
        process.exit(1);
      }
    }

    return promptGenerators;
  } catch (error) {
    logger.error(`Failed to load prompt.txt: ${error.message}`);
    process.exit(1);
  }
};

const getRandomPrompt = (agentName, promptGenerators) => {
  const prompts = promptGenerators[agentName] || [];
  return prompts[Math.floor(Math.random() * prompts.length)];
};

const userAgent = new UserAgent();
const baseHeaders = {
  'Accept': 'application/json, text/plain, */*',
  'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
  'Origin': 'https://testnet.gokite.ai',
  'Referer': 'https://testnet.gokite.ai/',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-site',
  'User-Agent': userAgent.toString(),
  'Content-Type': 'application/json'
};

const KITE_AI_SUBNET = '0xb132001567650917d6bd695d1fab55db7986e9a5';

const getWallet = (privateKey) => {
  try {
    const wallet = new ethers.Wallet(privateKey);
    logger.info(`Wallet created: ${wallet.address}`);
    return wallet;
  } catch (error) {
    logger.error(`Invalid private key: ${error.message}`);
    return null;
  }
};

const encryptAddress = (address) => {
  try {
    const keyHex = '6a1c35292b7c5b769ff47d89a17e7bc4f0adfe1b462981d28e0e9f7ff20b8f8a';
    const key = Buffer.from(keyHex, 'hex');
    const iv = crypto.randomBytes(12);
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    
    let encrypted = cipher.update(address, 'utf8');
    encrypted = Buffer.concat([encrypted, cipher.final()]);
    const authTag = cipher.getAuthTag();
    
    const result = Buffer.concat([iv, encrypted, authTag]);
    return result.toString('hex');
  } catch (error) {
    logger.error(`Auth token generation failed for ${address}`);
    return null;
  }
};

const extractCookies = (headers) => {
  try {
    const rawCookies = headers['set-cookie'] || [];
    const skipKeys = ['expires', 'path', 'domain', 'samesite', 'secure', 'httponly', 'max-age'];
    const cookiesDict = {};
    
    for (const cookieStr of rawCookies) {
      const parts = cookieStr.split(';');
      for (const part of parts) {
        const cookie = part.trim();
        if (cookie.includes('=')) {
          const [name, value] = cookie.split('=', 2);
          if (name && value && !skipKeys.includes(name.toLowerCase())) {
            cookiesDict[name] = value;
          }
        }
      }
    }
    
    return Object.entries(cookiesDict).map(([key, value]) => `${key}=${value}`).join('; ') || null;
  } catch (error) {
    return null;
  }
};

const solveRecaptcha = async (url, apiKey, maxRetries = 3) => {
  const siteKey = '6Lc_VwgrAAAAALtx_UtYQnW-cFg8EPDgJ8QVqkaz';
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      logger.loading(`Solving reCAPTCHA with 2Captcha (Attempt ${attempt}/${maxRetries})`);
      
      const requestUrl = `http://2captcha.com/in.php?key=${apiKey}&method=userrecaptcha&googlekey=${siteKey}&pageurl=${url}&json=1`;
      const requestResponse = await axios.get(requestUrl);
      
      if (requestResponse.data.status !== 1) {
        logger.error(`Failed to submit reCAPTCHA task: ${requestResponse.data.error_text}`);
        if (attempt === maxRetries) return null;
        await new Promise(resolve => setTimeout(resolve, 5000));
        continue;
      }
      
      const requestId = requestResponse.data.request;
      logger.step(`reCAPTCHA task submitted, ID: ${requestId}`);
      
      let pollAttempts = 0;
      const maxPollAttempts = 30;
      const pollInterval = 5000;
      
      while (pollAttempts < maxPollAttempts) {
        await new Promise(resolve => setTimeout(resolve, pollInterval));
        const resultUrl = `http://2captcha.com/res.php?key=${apiKey}&action=get&id=${requestId}&json=1`;
        const resultResponse = await axios.get(resultUrl);
        
        if (resultResponse.data.status === 1) {
          logger.success('reCAPTCHA solved successfully');
          return resultResponse.data.request;
        }
        
        if (resultResponse.data.request === 'ERROR_CAPTCHA_UNSOLVABLE') {
          logger.error('reCAPTCHA unsolvable');
          if (attempt === maxRetries) return null;
          break;
        }
        
        pollAttempts++;
        logger.step(`Waiting for reCAPTCHA solution (Attempt ${pollAttempts}/${maxPollAttempts})`);
      }
    } catch (error) {
      logger.error(`reCAPTCHA solving error: ${error.message}`);
      if (attempt === maxRetries) return null;
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }
  
  logger.error('reCAPTCHA solving failed after maximum retries');
  return null;
};

const claimDailyFaucet = async (access_token, cookieHeader, apiKey) => {
  try {
    logger.loading('Attempting to claim daily faucet...');
    
    const pageUrl = 'https://testnet.gokite.ai';
    const recaptchaToken = await solveRecaptcha(pageUrl, apiKey);
    
    if (!recaptchaToken) {
      logger.error('Failed to obtain reCAPTCHA token');
      return false;
    }
    
    const faucetHeaders = {
      ...baseHeaders,
      Authorization: `Bearer ${access_token}`,
      'x-recaptcha-token': recaptchaToken
    };
    
    if (cookieHeader) {
      faucetHeaders['Cookie'] = cookieHeader;
    }
    
    const response = await axios.post('https://ozone-point-system.prod.gokite.ai/blockchain/faucet-transfer', {}, {
      headers: faucetHeaders
    });
    
    if (response.data.error) {
      logger.error(`Faucet claim failed: ${response.data.error}`);
      return false;
    }
    
    logger.success('Daily faucet claimed successfully');
    return true;
  } catch (error) {
    logger.error(`Faucet claim error: ${error.response?.data?.error || error.message}`);
    return false;
  }
};

const getStakeInfo = async (access_token, cookieHeader) => {
  try {
    logger.loading('Fetching stake information...');
    
    const stakeHeaders = {
      ...baseHeaders,
      Authorization: `Bearer ${access_token}`
    };
    
    if (cookieHeader) {
      stakeHeaders['Cookie'] = cookieHeader;
    }
    
    const response = await axios.get('https://ozone-point-system.prod.gokite.ai/subnet/3/staked-info?id=3', {
      headers: stakeHeaders
    });
    
    if (response.data.error) {
      logger.error(`Failed to fetch stake info: ${response.data.error}`);
      return null;
    }
    
    return response.data.data;
  } catch (error) {
    logger.error(`Stake info fetch error: ${error.response?.data?.error || error.message}`);
    return null;
  }
};

const stakeToken = async (access_token, cookieHeader, maxRetries = 5) => {
  try {
    logger.loading('Attempting to stake 1 KITE token...');
    
    const stakeHeaders = {
      ...baseHeaders,
      Authorization: `Bearer ${access_token}`
    };
    
    if (cookieHeader) {
      stakeHeaders['Cookie'] = cookieHeader;
    }
    
    const payload = {
      subnet_address: KITE_AI_SUBNET,
      amount: 1
    };
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await axios.post('https://ozone-point-system.prod.gokite.ai/subnet/delegate', payload, {
          headers: stakeHeaders
        });
        
        if (response.data.error) {
          logger.error(`Stake failed: ${response.data.error}`);
          return false;
        }
        
        logger.success(`Successfully staked 1 KITE token`);
        return true;
      } catch (error) {
        if (attempt === maxRetries) {
          logger.error(`Stake error after ${maxRetries} attempts: ${error.response?.data?.error || error.message}`);
          return false;
        }
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    }
  } catch (error) {
    logger.error(`Stake error: ${error.response?.data?.error || error.message}`);
    return false;
  }
};

const claimStakeRewards = async (access_token, cookieHeader, maxRetries = 5) => {
  try {
    logger.loading('Attempting to claim stake rewards...');
    
    const claimHeaders = {
      ...baseHeaders,
      Authorization: `Bearer ${access_token}`
    };
    
    if (cookieHeader) {
      claimHeaders['Cookie'] = cookieHeader;
    }
    
    const payload = {
      subnet_address: KITE_AI_SUBNET
    };
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await axios.post('https://ozone-point-system.prod.gokite.ai/subnet/claim-rewards', payload, {
          headers: claimHeaders
        });
        
        if (response.data.error) {
          logger.error(`Claim rewards failed: ${response.data.error}`);
          return false;
        }
        
        const reward = response.data.data?.claim_amount || 0;
        logger.success(`Successfully claimed ${reward} KITE rewards`);
        return true;
      } catch (error) {
        if (attempt === maxRetries) {
          logger.error(`Claim rewards error after ${maxRetries} attempts: ${error.response?.data?.error || error.message}`);
          return false;
        }
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    }
  } catch (error) {
    logger.error(`Claim rewards error: ${error.response?.data?.error || error.message}`);
    return false;
  }
};

const login = async (wallet, neo_session = null, refresh_token = null, maxRetries = 3) => {
  const url = 'https://neo.prod.gokite.ai/v2/signin';
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      logger.loading(`Logging in to ${wallet.address} (Attempt ${attempt}/${maxRetries})`);

      const authToken = encryptAddress(wallet.address);
      if (!authToken) return null;
      
      const loginHeaders = {
        ...baseHeaders,
        'Authorization': authToken,
      };

      if (neo_session || refresh_token) {
        const cookies = [];
        if (neo_session) cookies.push(`neo_session=${neo_session}`);
        if (refresh_token) cookies.push(`refresh_token=${refresh_token}`);
        loginHeaders['Cookie'] = cookies.join('; ');
      }
      
      const body = { eoa: wallet.address };
      const response = await axios.post(url, body, { headers: loginHeaders });
      
      if (response.data.error) {
        logger.error(`Login failed for ${wallet.address}: ${response.data.error}`);
        return null;
      }
      
      const { access_token, aa_address, displayed_name, avatar_url } = response.data.data;
      const cookieHeader = extractCookies(response.headers);

      let resolved_aa_address = aa_address;
      if (!resolved_aa_address) {
        const profile = await getUserProfile(access_token);
        resolved_aa_address = profile?.profile?.smart_account_address;
        if (!resolved_aa_address) {
          logger.error(`No aa_address found for ${wallet.address}`);
          return null;
        }
      }
      
      logger.success(`Login successful for ${wallet.address}`);
      return { access_token, aa_address: resolved_aa_address, displayed_name, avatar_url, cookieHeader };
    } catch (error) {
      const errorMessage = error.response?.data?.error || error.message;
      if (attempt === maxRetries) {
        logger.error(`Login failed for ${wallet.address} after ${maxRetries} attempts: ${errorMessage}. Check cookies or contact Kite AI support.`);
        return null;
      }
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
};

const getUserProfile = async (access_token) => {
  try {
    const response = await axios.get('https://ozone-point-system.prod.gokite.ai/me', {
      headers: { ...baseHeaders, Authorization: `Bearer ${access_token}` }
    });
    
    if (response.data.error) {
      logger.error(`Failed to fetch profile: ${response.data.error}`);
      return null;
    }
    
    return response.data.data;
  } catch (error) {
    logger.error(`Profile fetch error: ${error.message}`);
    return null;
  }
};

const interactWithAgent = async (access_token, aa_address, cookieHeader, agent, prompt, interactionCount) => {
  try {
    if (!aa_address) {
      logger.error(`Cannot interact with ${agent.name}: No aa_address`);
      return null;
    }
    
    logger.step(`Interaction ${interactionCount} - Prompts : ${prompt}`);

    const inferenceHeaders = {
      ...baseHeaders,
      Authorization: `Bearer ${access_token}`,
      Accept: 'text/event-stream'
    };
    if (cookieHeader) {
      inferenceHeaders['Cookie'] = cookieHeader;
    }
    
    const inferenceResponse = await axios.post('https://ozone-point-system.prod.gokite.ai/agent/inference', {
      service_id: agent.service_id,
      subnet: 'kite_ai_labs',
      stream: true,
      body: { stream: true, message: prompt }
    }, {
      headers: inferenceHeaders
    });

    let output = '';
    const lines = inferenceResponse.data.split('\n');
    for (const line of lines) {
      if (line.startsWith('data: ') && line !== 'data: [DONE]') {
        try {
          const data = JSON.parse(line.replace('data: ', ''));
          if (data.choices && data.choices[0].delta.content) {
            output += data.choices[0].delta.content;
            if (output.length > 100) {
              output = output.substring(0, 100) + '...';
              break;
            }
          }
        } catch (e) {}
      }
    }

    const receiptHeaders = {
      ...baseHeaders,
      Authorization: `Bearer ${access_token}`
    };
    if (cookieHeader) {
      receiptHeaders['Cookie'] = cookieHeader;
    }
    
    const receiptResponse = await axios.post('https://neo.prod.gokite.ai/v2/submit_receipt', {
      address: aa_address,
      service_id: agent.service_id,
      input: [{ type: 'text/plain', value: prompt }],
      output: [{ type: 'text/plain', value: output || 'No response' }]
    }, {
      headers: receiptHeaders
    });
    
    if (receiptResponse.data.error) {
      logger.error(`Receipt submission failed for ${agent.name}: ${receiptResponse.data.error}`);
      return null;
    }
    
    const { id } = receiptResponse.data.data;
    logger.step(`Interaction ${interactionCount} - Receipt submitted, ID: ${id}`);

    let statusResponse;
    let attempts = 0;
    const maxAttempts = 10;
    while (attempts < maxAttempts) {
      statusResponse = await axios.get(`https://neo.prod.gokite.ai/v1/inference?id=${id}`, {
        headers: { ...baseHeaders, Authorization: `Bearer ${access_token}` }
      });
      
      if (statusResponse.data.data.processed_at && statusResponse.data.data.tx_hash) {
        logger.step(`Interaction ${interactionCount} - Inference processed, tx_hash : ${statusResponse.data.data.tx_hash}`);
        return statusResponse.data.data;
      }
      
      attempts++;
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    logger.error(`Inference status not completed after ${maxAttempts} attempts`);
    return null;
  } catch (error) {
    logger.error(`Error interacting with ${agent.name}: ${error.response?.data?.error || error.message}`);
    return null;
  }
};

const getNextRunTime = () => {
  const now = new Date();
  now.setHours(now.getHours() + 24);
  now.setMinutes(0);
  now.setSeconds(0);
  now.setMilliseconds(0);
  return now;
};

const displayCountdown = (nextRunTime, interactionCount, apiKey) => {
  const updateCountdown = () => {
    const now = new Date();
    const timeLeft = nextRunTime - now;
    
    if (timeLeft <= 0) {
      logger.info('Starting new daily run...');
      clearInterval(countdownInterval);
      dailyRun(interactionCount, apiKey); 
      return;
    }

    const hours = Math.floor(timeLeft / (1000 * 60 * 60));
    const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
    
    process.stdout.write(`\r${colors.cyan}[⏰] Next run in: ${hours}h ${minutes}m ${seconds}s${colors.reset} `);
  };

  updateCountdown();
  const countdownInterval = setInterval(updateCountdown, 1000);
};

let interactionCount = null;
let apiKey = null;

const dailyRun = async (count, key) => {
  logger.banner();
  
  const promptGenerators = await loadPrompts();
  
  const wallets = Object.keys(process.env)
    .filter(key => key.startsWith('PRIVATE_KEY_'))
    .map(key => ({
      privateKey: process.env[key],
      neo_session: process.env[`NEO_SESSION_${key.split('_')[2]}`] || null,
      refresh_token: process.env[`REFRESH_TOKEN_${key.split('_')[2]}`] || null
    }))
    .filter(wallet => wallet.privateKey && wallet.privateKey.trim() !== '');
  
  if (wallets.length === 0) {
    logger.error('No valid private keys found in .env');
    return;
  }

  if (interactionCount === null) {
    interactionCount = await new Promise((resolve) => {
      readline.question('Enter the number of interactions per agent: ', (answer) => {
        const count = parseInt(answer);
        if (isNaN(count) || count < 1 || count > 99999) {
          logger.error('Invalid input. Please enter a number between 1 and 99999.');
          process.exit(1);
        }
        resolve(count);
      });
    });
  }

  if (apiKey === null) {
    apiKey = await new Promise((resolve) => {
      readline.question('Enter your 2Captcha API key (press Enter to skip faucet claim): ', (answer) => {
        resolve(answer.trim() || null);
      });
    });
  }

  for (const { privateKey, neo_session, refresh_token } of wallets) {
    const wallet = getWallet(privateKey);
    if (!wallet) continue;
    
    logger.wallet(`Processing wallet: ${wallet.address}`);

    const loginData = await login(wallet, neo_session, refresh_token);
    if (!loginData) continue;
    
    const { access_token, aa_address, displayed_name, cookieHeader } = loginData;
    if (!aa_address) continue;

    const profile = await getUserProfile(access_token);
    if (!profile) continue;

    logger.info(`User: ${profile.profile.displayed_name || displayed_name || 'Unknown'}`);
    logger.info(`EOA Address: ${profile.profile.eoa_address || wallet.address}`);
    logger.info(`Smart Account: ${profile.profile.smart_account_address || aa_address}`);
    logger.info(`Total XP Points: ${profile.profile.total_xp_points || 0}`);
    logger.info(`Referral Code: ${profile.profile.referral_code || 'None'}`);
    logger.info(`Badges Minted: ${profile.profile.badges_minted?.length || 0}`);
    logger.info(`Twitter Connected: ${profile.social_accounts?.twitter?.id ? 'Yes' : 'No'}`);

    const stakeInfo = await getStakeInfo(access_token, cookieHeader);
    if (stakeInfo) {
      logger.info(`----- Stake Information -----`);
      logger.info(`My Staked Amount: ${stakeInfo.my_staked_amount} tokens`);
      logger.info(`Total Staked Amount: ${stakeInfo.staked_amount} tokens`);
      logger.info(`Delegator Count: ${stakeInfo.delegator_count}`);
      logger.info(`APR: ${stakeInfo.apr}%`);
      logger.info(`-----------------------------`);
    }

    if (apiKey) {
      await claimDailyFaucet(access_token, cookieHeader, apiKey);
    } else {
      logger.info('Skipping faucet claim (no 2Captcha API key provided)');
    }

    await stakeToken(access_token, cookieHeader);

    await claimStakeRewards(access_token, cookieHeader);

    for (const agent of agents) {
      const agentHeader = agent.name === 'Professor' ? '\n----- PROFESSOR -----' : 
                         agent.name === 'Crypto Buddy' ? '----- CRYPTO BUDDY -----' : 
                         '----- SHERLOCK -----';
      logger.agent(`${agentHeader}`);
      
      for (let i = 0; i < interactionCount; i++) {
        const prompt = getRandomPrompt(agent.name, promptGenerators);
        await interactWithAgent(access_token, aa_address, cookieHeader, agent, prompt, i + 1);
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
      logger.agent('\n'); 
    }
  }
  
  logger.success('Bot execution completed');
  const nextRunTime = getNextRunTime();
  logger.info(`Next run scheduled at: ${nextRunTime.toLocaleString()}`);
  displayCountdown(nextRunTime, interactionCount, apiKey);
};

const main = async () => {
  try {
    await dailyRun(interactionCount, apiKey);
  } catch (error) {
    logger.error(`Bot error: ${error.response?.data?.error || error.message}`);
    const nextRunTime = getNextRunTime();
    logger.info(`Next run scheduled at: ${nextRunTime.toLocaleString()}`);
    displayCountdown(nextRunTime, interactionCount, apiKey);
  }
};

main().catch(error => logger.error(`Bot error: ${error.response?.data?.error || error.message}`));
