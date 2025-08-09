import asyncio
import os
from typing import List, Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv
import json

load_dotenv()


class LLMService:
    def __init__(self):
        api_key = os.environ("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            print("⚠️  OpenAI API key not set. LLM features will be disabled.")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4"

    async def select_documents(
        self,
        description: str,
        documents: List[Dict[str, Any]],
        question: str,
        chat_history: List[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Select relevant documents based on description, question, and chat history"""

        if not self.client:
            # Fallback: return all documents when OpenAI is not available
            return documents

        doc_summaries = []
        for doc in documents:
            doc_summaries.append(
                {
                    "filename": doc["filename"],
                    "total_pages": doc["total_pages"],
                    "first_page_preview": doc["pages"][0]["text"][:500] + "...",
                }
            )

        # Format chat history
        history_context = ""
        if chat_history:
            history_context = "\n\nChat History:\n"
            for msg in chat_history[-5:]:  # Include last 5 messages for context
                if hasattr(msg, "role"):
                    role = msg.role
                    content = msg.content
                else:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                history_context += f"{role.capitalize()}: {content}\n"

        prompt = f"""
Based on the following document collection description, chat history, and current question, 
select which documents are most likely to contain the answer.

Document Collection Description: {description}

Available Documents:
{json.dumps(doc_summaries, indent=2)}
{history_context}
Current Question: {question}

Return a JSON array of filenames that are most relevant to the current question and conversation context.
Only return the JSON array, no other text.
Example: ["document1.pdf", "document2.pdf"]
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=[{"role": "user", "content": prompt}],
            )

            selected_filenames = json.loads(response.choices[0].message.content)

            # Return full document objects for selected filenames
            selected_docs = []
            for doc in documents:
                if doc["filename"] in selected_filenames:
                    selected_docs.append(doc)

            return selected_docs

        except Exception as e:
            print(f"Error in document selection: {e}")
            # Fallback: return all documents
            return documents

    async def find_relevant_pages(
        self,
        pages: List[Dict[str, Any]],
        question: str,
        filename: str,
        chat_history: List[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Find relevant pages by processing 20 pages at a time in parallel"""

        if not self.client:
            # Fallback: return first 3 pages when OpenAI is not available
            fallback_pages = []
            for page in pages[:3]:
                page_with_source = page.copy()
                page_with_source["source_document"] = filename
                fallback_pages.append(page_with_source)
            return fallback_pages

        # Create chunks of 20 pages
        chunks = []
        for i in range(0, len(pages), 20):
            chunk = pages[i : i + 20]
            chunks.append(chunk)

        # Process all chunks in parallel
        chunk_tasks = []
        for chunk_index, chunk in enumerate(chunks):
            task = self._process_page_chunk(
                chunk, question, filename, chunk_index, chat_history
            )
            chunk_tasks.append(task)

        # Wait for all chunks to complete
        chunk_results = await asyncio.gather(*chunk_tasks, return_exceptions=True)

        # Combine results from all chunks
        relevant_pages = []
        for result in chunk_results:
            if isinstance(result, Exception):
                print(f"Error in chunk processing: {result}")
                continue
            if isinstance(result, list):
                relevant_pages.extend(result)

        return relevant_pages

    async def _process_page_chunk(
        self,
        chunk: List[Dict[str, Any]],
        question: str,
        filename: str,
        chunk_index: int,
        chat_history: List[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Process a single chunk of pages"""
        import time

        chunk_start = time.time()
        print(f"    🔍 Processing chunk {chunk_index + 1} with {len(chunk)} pages...")

        # Prepare content for LLM
        pages_content = []
        for page in chunk:
            pages_content.append(
                {
                    "page_number": page["page_number"],
                    "text": (
                        page["text"][:1000] + "..."
                        if len(page["text"]) > 1000
                        else page["text"]
                    ),
                }
            )

        # Format chat history for context
        history_context = ""
        if chat_history:
            history_context = "\n\nRecent Chat History:\n"
            for msg in chat_history[-3:]:  # Include last 3 messages for context
                if hasattr(msg, "role"):
                    role = msg.role
                    content = msg.content[:200]  # Truncate for context
                else:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")[:200]  # Truncate for context
                history_context += f"{role.capitalize()}: {content}...\n"

        prompt = f"""
Analyze the following pages from document "{filename}" and determine 
which pages are relevant to the current question, considering the conversation context.

{history_context}
Current Question: {question}

Pages:
{json.dumps(pages_content, indent=2)}

Return a JSON array of page numbers that are relevant to the current question and conversation context.
Only return the JSON array, no other text.
Example: [1, 3, 5]
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=[{"role": "user", "content": prompt}],
            )

            relevant_page_numbers = json.loads(response.choices[0].message.content)

            # Add full page data for relevant pages
            relevant_pages = []
            for page in chunk:
                if page["page_number"] in relevant_page_numbers:
                    page_with_source = page.copy()
                    page_with_source["source_document"] = filename
                    relevant_pages.append(page_with_source)

            chunk_time = time.time() - chunk_start
            print(
                f"    ✅ Chunk {chunk_index + 1} completed in {chunk_time:.2f}s, found {len(relevant_pages)} relevant pages"
            )
            return relevant_pages

        except Exception as e:
            chunk_time = time.time() - chunk_start
            print(f"    ❌ Chunk {chunk_index + 1} failed in {chunk_time:.2f}s: {e}")
            # Fallback: include first page of chunk
            if chunk:
                first_page = chunk[0].copy()
                first_page["source_document"] = filename
                return [first_page]
            return []

    async def generate_answer(
        self, relevant_pages: List[Dict[str, Any]], question: str
    ) -> str:
        """Generate final answer using all relevant pages (non-streaming)"""

        if not relevant_pages:
            return "I couldn't find any relevant information to answer your question."

        if not self.client:
            # Fallback response when OpenAI is not available
            context_preview = ""
            for page in relevant_pages[:2]:
                context_preview += (
                    f"From {page['source_document']} (Page {page['page_number']}): "
                )
                context_preview += page["text"][:200] + "...\n\n"

            return f"""**OpenAI API not configured - showing document preview:**

Question: {question}

Relevant content found:
{context_preview}

To get AI-powered answers, please set your OpenAI API key in backend/.env file:
OPENAI_API_KEY=your_actual_api_key_here"""

        # Prepare content from all relevant pages
        context = ""
        for page in relevant_pages:
            context += (
                f"\n--- Page {page['page_number']} from {page['source_document']} ---\n"
            )
            context += page["text"]
            context += "\n"

        prompt = f"""
Based on the following context from PDF documents, answer the question. 
Provide answer and cite which documents and pages you're referencing.

IMPORTANT: When referencing specific pages, use this special format:
$PAGE_START{{filename}}:{{page_numbers}}$PAGE_END

Examples:
- For single page: $PAGE_STARTreport.pdf:5$PAGE_END
- For multiple pages: $PAGE_STARTanalysis.pdf:2,7,12$PAGE_END 
- For page range: $PAGE_STARTmanual.pdf:15-18$PAGE_END

Context:
{context}

Question: {question}

Please provide answer based on the information in the documents and use the special page reference format when citing specific pages.
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=[{"role": "user", "content": prompt}],
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error generating answer: {str(e)}"

    async def generate_answer_stream(
        self,
        relevant_pages: List[Dict[str, Any]],
        question: str,
        chat_history: List[Dict[str, Any]] = None,
    ):
        """Generate final answer using all relevant pages with streaming"""

        if not relevant_pages:
            yield "I couldn't find any relevant information to answer your question."
            return

        if not self.client:
            # Fallback response when OpenAI is not available
            context_preview = ""
            for page in relevant_pages[:2]:
                context_preview += (
                    f"From {page['source_document']} (Page {page['page_number']}): "
                )
                context_preview += page["text"][:200] + "...\n\n"

            fallback_text = f"""**OpenAI API not configured - showing document preview:**

Question: {question}

Relevant content found:
{context_preview}

To get AI-powered answers, please set your OpenAI API key in backend/.env file:
OPENAI_API_KEY=your_actual_api_key_here"""

            # Simulate streaming for fallback
            for char in fallback_text:
                yield char
                await asyncio.sleep(0.01)  # Small delay to simulate streaming
            return

        # Prepare content from all relevant pages
        context = ""
        for page in relevant_pages:
            context += (
                f"\n--- Page {page['page_number']} from {page['source_document']} ---\n"
            )
            context += page["text"]
            context += "\n"

        # Format chat history for conversational context
        history_context = ""
        if chat_history:
            history_context = "\n\nConversation History:\n"
            for msg in chat_history[-4:]:  # Include last 4 messages for context
                if hasattr(msg, "role"):
                    role = msg.role
                    content = msg.content
                else:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                history_context += f"{role.capitalize()}: {content}\n"

        prompt = f"""
Based on the following context from PDF documents and the conversation history, answer the current question. 
Provide a comprehensive answer that builds on the conversation and cite which documents and pages you're referencing.

IMPORTANT: When referencing specific pages, use this special format:
$PAGE_START{{filename}}:{{page_numbers}}$PAGE_END

Examples:
- For single page: $PAGE_STARTreport.pdf:5$PAGE_END
- For multiple pages: $PAGE_STARTanalysis.pdf:2,7,12$PAGE_END 
- For page range: $PAGE_STARTmanual.pdf:15-18$PAGE_END

Document Context:
{context}
{history_context}
Current Question: {question}

Please provide a answer based on the information in the documents and the conversation context.
If this question relates to previous questions in the conversation, acknowledge that connection.
Use the special page reference format whenever citing specific pages.
"""

        try:
            stream = await self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"Error generating answer: {str(e)}"
