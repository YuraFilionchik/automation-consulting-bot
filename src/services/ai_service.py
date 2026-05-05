"""AI сервис для консультаций (Google Gemini API)"""

import logging
import json
import re
from typing import List, Dict, Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from src.config.settings import settings

logger = logging.getLogger(__name__)


# Системный промпт
SYSTEM_PROMPT = """You are an AI consultant at "Automation Consulting", specializing in business process automation.

Your expertise:
- Telegram bots for business
- CRM systems (HubSpot, Pipedrive, Bitrix24, AmoCRM)
- Service integrations
- Data parsing and collection
- No-code automation (Make, n8n, Zapier)

LANGUAGE RULE:
- ALWAYS respond in the same language the user writes in.
- If user writes in English → reply in English.
- If user writes in Polish → reply in Polish.
- If user writes in Russian → reply in Russian.
- If user writes in Ukrainian → reply in Ukrainian.
- If user writes in German → reply in German.
- If language is unclear, default to English.

Communication rules:
1. Be professional and friendly
2. Ask 1-2 questions at a time, don't overwhelm
3. Give concrete examples from practice
4. Use emojis moderately
5. Write short paragraphs (2-4 sentences)

What you CAN do:
- Give rough budget estimates (ranges in EUR for Poland/Europe)
- Suggest solution options
- Explain technical things in simple language
- Suggest leaving an application for detailed assessment

What you CANNOT do:
- Give exact prices without full scope
- Promise specific timelines
- Use too much technical jargon
- Pretend to be a human

Budget reference (Poland/Europe):
- Simple project: €500–1,500
- Mid-range: €1,500–5,000
- Complex: €5,000–15,000+

If the client clearly states they want to leave an application, or if you have enough information to suggest one, start your response with "APPLICATION_REQUEST" on a separate line, then continue with your message. Be sure to ask the user explicitly if they would like to file a formal application."""


class AIService:
    """Сервис для работы с Google Gemini AI"""

    def __init__(self):
        # Инициализация Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)

        self.model = genai.GenerativeModel(
            model_name=settings.AI_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )

        self.generation_config = {
            "temperature": settings.AI_TEMPERATURE,
            "max_output_tokens": settings.AI_MAX_TOKENS,
        }

        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    async def get_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Получить ответ от Gemini AI"""

        try:
            # Построить промпт с историей
            prompt_parts = []

            if conversation_history:
                for msg in conversation_history[-20:]:
                    role = msg["role"]
                    content = msg["content"]
                    if role == "user":
                        prompt_parts.append(f"User: {content}")
                    elif role == "assistant":
                        prompt_parts.append(f"Assistant: {content}")

            prompt_parts.append(f"User: {user_message}")

            full_prompt = "\n".join(prompt_parts)

            # Вызов Gemini
            response = await self._generate(full_prompt)

            logger.info(f"AI response generated: {len(response)} chars")
            return response

        except Exception as e:
            logger.error(f"Error getting AI response: {e}", exc_info=True)
            return (
                "⚠️ Sorry, the AI consultant is temporarily unavailable. "
                "Please try again later or leave an application — "
                "our specialist will contact you!"
            )

    async def _generate(self, prompt: str) -> str:
        """Асинхронная генерация через Gemini"""

        import asyncio

        def _call():
            return self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
            )

        # Запустить в пуле потоков (Gemini SDK не асинхронный)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _call)

        if result and result.text:
            return result.text.strip()
        return "I'm sorry, I couldn't generate a response. Please try again."

    async def analyze_application(self, application_data: dict) -> str:
        """Анализировать заявку"""

        prompt = (
            f"Analyze this client application and provide:\n\n"
            f"1. Project type: {application_data.get('project_type', 'Not specified')}\n"
            f"2. Complexity (1-10): estimate based on description\n"
            f"3. Approximate budget category (EUR)\n"
            f"4. What technologies might be suitable\n"
            f"5. What clarifying questions could be asked\n\n"
            f"Application:\n"
            f"{application_data}\n\n"
            f"Respond in the same language the client used."
        )

        try:
            return await self._generate(prompt)
        except Exception as e:
            logger.error(f"Error analyzing application: {e}", exc_info=True)
            return "Analysis temporarily unavailable."

    async def extract_application_data(self, conversation_history: List[Dict[str, str]]) -> Dict:
        """Извлечь данные для заявки из истории диалога"""

        history_text = ""
        for msg in conversation_history:
            role = msg["role"]
            content = msg["content"]
            history_text += f"{role.capitalize()}: {content}\n"

        prompt = (
            f"Based on the following conversation history, extract information for a project application. "
            f"Return the data in JSON format with the following keys:\n"
            f"- project_type (possible values: bot, crm, website, parsing, other)\n"
            f"- project_subtype (relevant if project_type is bot: broadcast, lead_form, integration, chatbot, other)\n"
            f"- budget_range (e.g., 'under €500', '€500–1,500', '€1,500–5,000', '€5,000–15,000', '€15,000+')\n"
            f"- timeline (e.g., 'This week', 'This month', 'This quarter', 'Just planning')\n"
            f"- contact_info (any phone, email or username provided)\n"
            f"- task_description (a concise summary of the project goals and requirements)\n\n"
            f"If a piece of information is missing, use null for that field.\n\n"
            f"Conversation history:\n{history_text}\n\n"
            f"Return ONLY the JSON object."
        )

        try:
            response = await self._generate(prompt)
            # Извлечь JSON из ответа (на случай, если AI добавил лишний текст)

            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data
            return {}
        except Exception as e:
            logger.error(f"Error extracting application data: {e}", exc_info=True)
            return {}


# Глобальный экземпляр
ai_service = AIService()
