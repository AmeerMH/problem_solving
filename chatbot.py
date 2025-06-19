
import google.generativeai as genai
import requests
import tiktoken  # Add this import for token calculation
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json


class Chatbot:
    def __init__(self):
        # Configure the API key
        genai.configure(api_key="AIzaSyBBfWJ2Ha5KRKpvRJ2-J0DhwZWm_MWU9zc")
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        self.conversation_history = []
        self.token_count = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT encoding
        
        # Initialize Firebase
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Initialize Firebase Admin SDK
                cred = credentials.Certificate("chatbot-system-517be-firebase-adminsdk-hdya3-4b68866361.json")
                firebase_admin.initialize_app(cred)
                print("Firebase initialized successfully")
            else:
                print("Firebase already initialized")
            
            self.db = firestore.client()
            self.firebase_initialized = True
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self.firebase_initialized = False

    def set_company_id(self, company_id):
        """Set the company ID for API calls"""
        self.company_id = company_id
        self.api_base_url = f"https://apisv5.logestechs.com/api/guests/{company_id}/packages/tracking?barcode="

    def collect_data(self, stage: str, prompt: str, response: str, metadata: dict = None):
        """Collect data for model training"""
        data = {
            "stage": stage,
            "prompt": prompt,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "company_id": getattr(self, 'company_id', 410),  # Include company_id in data
            "metadata": metadata or {}
        }
        
        # Try Firebase first
        if self.firebase_initialized:
            try:
                collection_name = f"training_data_{stage}"
                self.db.collection(collection_name).add(data)
                print(f"Data collected for stage: {stage} (Firebase)")
                return
            except Exception as e:
                print(f"Firebase collection failed: {e}")
        
        # Fallback to local storage
        try:
            import os
            import json
            
            # Create data directory if it doesn't exist
            os.makedirs("training_data", exist_ok=True)
            
            # Save to local JSON file
            filename = f"training_data/training_data_{stage}.json"
            
            # Load existing data or create new list
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            else:
                existing_data = []
            
            # Add new data
            existing_data.append(data)
            
            # Save back to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            print(f"Data collected for stage: {stage} (Local)")
            
        except Exception as e:
            print(f"Local collection failed: {e}")

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        return len(self.encoding.encode(text))

    def update_token_count(self, prompt_tokens: int, completion_tokens: int):
        """Update the token count for the conversation and collect token usage data."""
        self.token_count["prompt_tokens"] += prompt_tokens
        self.token_count["completion_tokens"] += completion_tokens
        self.token_count["total_tokens"] = self.token_count["prompt_tokens"] + self.token_count["completion_tokens"]
        
        # Collect token usage data
        self.collect_token_usage(prompt_tokens, completion_tokens)

    def collect_token_usage(self, prompt_tokens: int, completion_tokens: int):
        """Collect token usage data for monitoring and cost analysis"""
        try:
            token_data = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "timestamp": datetime.now().isoformat(),
                "company_id": getattr(self, 'company_id', 410),  # Include company_id in token data
                "estimated_cost": {
                    "prompt_cost": prompt_tokens * 0.00001,  # $0.01 per 1K tokens
                    "completion_cost": completion_tokens * 0.00002,  # $0.02 per 1K tokens
                    "total_cost": (prompt_tokens * 0.00001) + (completion_tokens * 0.00002)
                },
                "model": "gemini-2.0-flash-exp",
                "session_total_tokens": self.token_count["total_tokens"]
            }
            
            # Try Firebase first
            if self.firebase_initialized:
                try:
                    self.db.collection("token_usage").add(token_data)
                    print(f"Token usage collected: {prompt_tokens + completion_tokens} tokens")
                    return
                except Exception as e:
                    print(f"Firebase token collection failed: {e}")
            
            # Fallback to local storage
            try:
                import os
                import json
                
                # Create data directory if it doesn't exist
                os.makedirs("training_data", exist_ok=True)
                
                # Save to local JSON file
                filename = "training_data/token_usage.json"
                
                # Load existing data or create new list
                if os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                else:
                    existing_data = []
                
                # Add new data
                existing_data.append(token_data)
                
                # Save back to file
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)
                
                print(f"Token usage collected locally: {prompt_tokens + completion_tokens} tokens")
                
            except Exception as e:
                print(f"Local token collection failed: {e}")
                
        except Exception as e:
            print(f"Token usage collection failed: {e}")

    def get_token_count(self) -> dict:
        """Get the current token count statistics."""
        return self.token_count

    def extract_intent(self, prompt: str) -> str:
        intent_instruction = """the answer should be one word
        Here are some examples of user queries and their intents:
        - 'وين شحنتي؟' => shipment_tracking
        - 'أريد معرفة حالة طلبي' => order_status
        - 'ما هو رقم تتبعي؟' => tracking_number
        - 'هل تم شحن طلبي؟' => shipment_status
        - 'متى سيصل طلبي؟' => delivery_time
        - 'أين يمكنني استلام شحنتي؟' => pickup_location
        """
        
        response = self.model.generate_content(
            f"{intent_instruction}\n\nUser: {prompt}",
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                top_p=0.95,
                max_output_tokens=10,
            )
        )
        intent = response.text.strip().split(" ")[0]
        
        # Collect data for training
        self.collect_data(
            stage="extract_intent",
            prompt=prompt,
            response=intent,
            metadata={
                "instruction": intent_instruction,
                "model": "gemini-2.0-flash-exp",
                "temperature": 0,
                "max_tokens": 10
            }
        )
        
        return intent

    def extract_intent_stage_one(self, prompt: str) -> str:
        system_instruction = """
            Your task is to answer with only "yes" or "no".

            If the user is asking about the company's services (such as tracking, delivery, shipping, or support), respond with "yes". Otherwise, respond with "no".

            Here are some examples:

            User: "وين شحنتي؟"
            Answer: yes

            User: "كيف أتتبع طلبي؟"
            Answer: yes

            User: "شو بتقدموا خدمات؟"
            Answer: yes

            User: "شو رأيك في برشلونة؟"
            Answer: no

            User: "كيف الطقس اليوم؟"
            Answer: no

            User: "هل توصلوا للقدس؟"
            Answer: yes
            """
        
        response = self.model.generate_content(
            f"{system_instruction}\n\nUser: {prompt}",
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                top_p=0.95,
                max_output_tokens=10,
            )
        )
        intent = response.text.strip().split(" ")[0]
        
        # Collect data for training
        self.collect_data(
            stage="extract_intent_stage_one",
            prompt=prompt,
            response=intent,
            metadata={
                "instruction": system_instruction,
                "model": "gemini-2.0-flash-exp",
                "temperature": 0,
                "max_tokens": 10,
                "expected_values": ["yes", "no"]
            }
        )
        
        return intent

    def extract_tracking_number(self, prompt: str) -> str:
        tracking_instruction = """
        Your task is to extract a tracking number from the user's message, if one exists.
        Common tracking number formats include:
        - LT followed by 10 digits (e.g., LT1234567890)
        - 16 digit numbers (e.g., 1234567890123456)
        - Alphanumeric codes like AB123456789CD
        - 12 digit numbers starting with digits (e.g., 100298037303)

        If you find a tracking number, return just the tracking number.
        If no tracking number is found, return "NO_TRACKING_NUMBER".
        """
        
        response = self.model.generate_content(
            f"{tracking_instruction}\n\nUser: {prompt}",
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                top_p=0.95,
                max_output_tokens=20,
            )
        )
        tracking_number = response.text.strip()
        
        # Collect data for training
        self.collect_data(
            stage="extract_tracking_number",
            prompt=prompt,
            response=tracking_number,
            metadata={
                "instruction": tracking_instruction,
                "model": "gemini-2.0-flash-exp",
                "temperature": 0,
                "max_tokens": 20,
                "has_tracking_number": tracking_number != "NO_TRACKING_NUMBER"
            }
        )
        
        return tracking_number

    def fetch_shipment_data(self, tracking_number: str) -> dict:
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.get(f"{self.api_base_url}{tracking_number}", headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API returned status code {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to fetch shipment data: {str(e)}"}

    def generate_response(self, prompt: str) -> str:
        # Count prompt tokens
        prompt_tokens = self.count_tokens(prompt)
        
        def get_system_instruction(extra_info="") -> str:
            base_info = (
                "❗ ملاحظة: اسم الشركة معروف مسبقًا وهو \"LogesTechs\". لا تطلب من المستخدم توضيح اسم الشركة، ورد دائمًا وكأنك تمثل LogesTechs فقط.\n\n"
                "مرحبًا! 👋 أنت المساعد الذكي لشركة LogesTechs – شركة تكنولوجيا متطورة تأسست عام 2019، وتعمل على تطوير حلول ذكية ومبتكرة "
                "لإدارة التوصيل والمخزون في منطقة الشرق الأوسط وشمال أفريقيا. تقدم LogesTechs خدماتها لمجموعة واسعة من الشركات، من الناشئة إلى الكبيرة، "
                "لمساعدتها على تحسين الأداء، تقليل التكاليف، وزيادة رضا العملاء.\n\n"
                "تشمل خدماتنا:\n"
                "- تتبع الشحنات بدقة وشفافية\n"
                "- جدولة التوصيلات بكفاءة\n"
                "- إدارة المخزون بشكل ذكي\n"
                "- تقديم الدعم الفني للمستخدمين\n\n"
                "مهمتك كمساعد ذكي هي مساعدة العملاء والسائقين وفريق العمل من خلال تقديم معلومات دقيقة تتعلق حصريًا بخدمات ومنتجات LogesTechs. "
                "لا تقم بالرد على أي استفسارات خارج نطاق خدمات الشركة. إذا تم طرح سؤال خارج هذا النطاق، اعتذر بلطف وأوضح أنك متخصص فقط في دعم LogesTechs، "
                "وقم بتوجيه المستخدم للقسم المناسب إذا لزم الأمر.\n\n"
                "إذا تم سؤالك عن محتويات الشحنة، فكن شفافًا إذا توفرت المعلومات، وغالبًا ما تكون موجودة في خانة 'description'.\n\n"
                "❗ **مهم:** أجب على الأسئلة بنفس اللغة التي طُرحت بها. إذا كان السؤال بالعربية، أجب بالعربية. وإذا كان بالإنجليزية، أجب بالإنجليزية.\n\n"
                "خليك دائمًا واضح، مهني، وسريع — وساعد الكل بأفضل شكل ممكن!"
            )
            return base_info + (f"\n\nاستخدم هاذه المعلومات للاجابة: {extra_info}" if extra_info else "")

        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "parts": [{"text": prompt}]})

        is_relevant = self.extract_intent_stage_one(prompt)
        if is_relevant.lower() != "yes":
            response = "عذراً، أنا مساعد LogesTechs الذكي، وأستطيع مساعدتك فقط في أمور متعلقة بخدمات الشحن والتوصيل الخاصة بنا. هل لديك استفسار حول شحنة أو خدمات الشركة؟"
            self.conversation_history.append({"role": "model", "parts": [{"text": response}]})
            return response

        tracking_number = self.extract_tracking_number(prompt)

        if tracking_number != "NO_TRACKING_NUMBER":
            shipment_data = self.fetch_shipment_data(tracking_number)
            system_instruction = get_system_instruction(shipment_data)
            
            # Create chat session with conversation history (without system role)
            chat = self.model.start_chat(history=self.conversation_history)
            
            # Include system instruction in the prompt
            full_prompt = f"{system_instruction}\n\nUser: {prompt}"
            
            response = chat.send_message(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0,
                    top_p=0.95,
                    max_output_tokens=1092,
                )
            )
            
            response_text = response.text
            
            # Count completion tokens and update totals
            completion_tokens = self.count_tokens(response_text)
            self.update_token_count(prompt_tokens, completion_tokens)
            
            self.conversation_history.append({"role": "model", "parts": [{"text": response_text}]})
            return response_text

        elif self.extract_intent(prompt) == "shipment_tracking":
            response = "أهلاً بك في خدمة تتبع الشحنات من LogesTechs! 👋 \n\nيرجى تزويدي برقم التتبع الخاص بشحنتك (مثال: 100298037303) لكي أتمكن من مساعدتك في معرفة حالتها. 📦"
            self.conversation_history.append({"role": "model", "parts": [{"text": response}]})
            return response

        # For general queries
        self.conversation_history.append({"role": "user", "parts": [{"text": prompt}]})
        
        # Create chat session with conversation history (without system role)
        chat = self.model.start_chat(history=self.conversation_history)
        
        # Include system instruction in the prompt
        system_instruction = get_system_instruction()
        full_prompt = f"{system_instruction}\n\nUser: {prompt}"
        
        response = chat.send_message(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                top_p=0.95,
                max_output_tokens=1092,
            )
        )
        
        response_text = response.text
        
        # Count completion tokens and update totals
        completion_tokens = self.count_tokens(response_text)
        self.update_token_count(prompt_tokens, completion_tokens)
        
        self.conversation_history.append({"role": "model", "parts": [{"text": response_text}]})
        return response_text

    def reset_conversation(self):
        self.conversation_history = []
        return "تم إعادة المحادثة بنجاح. يمكنك البدء من جديد!"

    def get_conversation_history(self):
        return self.conversation_history
