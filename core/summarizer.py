import os

try:
    from langchain_mistralai import ChatMistralAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.runnables import RunnablePassthrough, RunnableLambda
except ImportError:
    ChatMistralAI = None
    ChatPromptTemplate = None
    StrOutputParser = None
    RecursiveCharacterTextSplitter = None
    RunnablePassthrough = None
    RunnableLambda = None


def get_llm():
    if ChatMistralAI is None:
        return None
    return ChatMistralAI(model="mistral-small-latest", mistral_api_key=os.getenv("MISTRAL_API_KEY"), temperature=0.3)


def split_transcript(transcript: str) -> list:
    if RecursiveCharacterTextSplitter is None:
        return [transcript]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 3000,
        chunk_overlap = 200
    )

    return splitter.split_text(transcript)

def summarize(transcript: str) -> str:
    if ChatPromptTemplate is None or StrOutputParser is None or RunnablePassthrough is None or RunnableLambda is None:
        return transcript.strip() or "No transcript available"

    llm = get_llm()
    if llm is None:
        return transcript.strip() or "No transcript available"

    map_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Summarize this portion of a meeting transcript concisely."),
            ("human", "{text}"),
        ]
    )

    map_chain = map_prompt | llm | StrOutputParser()

    chunks = split_transcript(transcript)
    chunk_summaries = [map_chain.invoke({"text": chunk}) for chunk in chunks]

    combined = "\n\n".join(chunk_summaries)

    combined_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert meeting summarizer. Combine these partial summaries "
                "into one final professional meeting summary in bullet points.",
            ),
            ("human", "{text}"),
        ]
    )

    combined_chain = (
        RunnablePassthrough() | RunnableLambda(lambda x: {"text": x}) | combined_prompt | llm | StrOutputParser()
    )

    return combined_chain.invoke(combined)


def generate_title(transcript: str) -> str:
    if ChatPromptTemplate is None or StrOutputParser is None or RunnablePassthrough is None or RunnableLambda is None:
        return "Untitled Analysis"

    llm = get_llm()
    if llm is None:
        return "Untitled Analysis"

    title_chain = (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Based on the meeting transcript, generate a short professional meeting title "
                    "(max 8 words). Only return the title, nothing else.",
                ),
                ("human", "{text}"),
            ]
        )
        | llm
        | StrOutputParser()
    )

    return title_chain.invoke(transcript[:2000])



