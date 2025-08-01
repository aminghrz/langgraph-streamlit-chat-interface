from langchain_core.messages import AIMessage, SystemMessage, BaseMessage, HumanMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_openai import ChatOpenAI

from typing import Literal, List
import streamlit as st

#↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ State class definition ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
class State(MessagesState):
    summary: str
#↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑ State class definition ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑

#↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ Node, conditional edge and tool definition ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
def call_model(state,react_agent_executor):
    summary = state.get("summary", "")
    current_messages = state["messages"]
    last_messages_to_send = current_messages[-5:] # Send last 5 actual messages

    messages_for_react_agent_input: List[BaseMessage] = []
    if summary:
    # The summary is prepended as a system message for context
        system_message_content = f"Here is a summary of the conversation so far: {summary}. Use this to inform your response."
        messages_for_react_agent_input.append(SystemMessage(content=system_message_content))

    messages_for_react_agent_input.extend(last_messages_to_send)

    # The ReAct agent expects input in the format {"messages": [list_of_messages]}
    # The last message in this list should be the one it needs to respond to (typically HumanMessage).
    agent_input = {"messages": messages_for_react_agent_input}

    # Invoke the ReAct agent.
    # Since there are no tools, it will essentially be an LLM call structured by the ReAct framework.
    # The react_agent_executor is already compiled.
    response_dict = react_agent_executor.invoke(agent_input)

    # The ReAct agent's response (AIMessage) will be in the 'messages' key of the output dictionary.
    # It's a list, and the agent's response is typically the last message added.
    ai_response_message = response_dict["messages"][-1]

    if not isinstance(ai_response_message, AIMessage):
        # Fallback or error handling if the last message isn't an AIMessage
        # This shouldn't happen in a typical ReAct flow without tool errors.
        st.error("ReAct agent did not return an AIMessage as expected.")
        return {"messages": [AIMessage(content="Sorry, I encountered an issue.")]}

    # The graph will automatically append the response to state["messages"]
    # We just need to return the new message to be added
    return {"messages": [ai_response_message]}

def summarize_conversation(state,chat_model):
        summary = state.get("summary", "")
        current_messages = state["messages"]
        # Let's use more messages for a better summary, e.g., last 6 (3 turns) that led to summarization
        # The last two messages are the AI response that triggered the summary, and the user message before that.
        # We want to summarize the conversation *before* the current turn that might be too long.
        messages_to_summarize = current_messages[:-2] # Exclude the last AI response and user query that triggered summary
        if len(messages_to_summarize) > 10 : # Cap the number of messages to summarize to avoid large prompts
            messages_to_summarize = messages_to_summarize[-10:]


        if not messages_to_summarize: # Nothing to summarize yet (e.g., if called too early)
            return {"summary": summary, "messages": []}


        summary_prompt_parts = []
        if summary:
            summary_prompt_parts.append(f"This is the current summary of the conversation: {summary}\n")

        summary_prompt_parts.append("Based on the following recent messages:\n")
        for msg in messages_to_summarize:
            if isinstance(msg, HumanMessage):
                summary_prompt_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                summary_prompt_parts.append(f"Assistant: {msg.content}")

        summary_prompt_parts.append("\nPlease update or create a concise summary of the entire conversation.")

        final_summary_prompt = "\n".join(summary_prompt_parts)

        # Construct messages for summarization
        messages_for_summary_llm = [HumanMessage(content=final_summary_prompt)]

        response = chat_model.invoke(messages_for_summary_llm)
        return {"summary": response.content, "messages": []}

def should_continue(state) -> Literal["summarize_conversation", END]: # type: ignore
    messages = state["messages"]
    if len(messages) > 6: 
        return "summarize_conversation"
    return END
#↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑ Node, conditional edge and tool definition ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑



#↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ Graph Definition ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
def create_graph(model, api_key, base_url, conn,):
    """Create and compile the LangGraph workflow"""
    
    chat_model = ChatOpenAI(
        temperature=0,
        model=model,
        api_key=api_key,
        base_url=base_url
    )

    prompt_content = ("You are a helpful assistant with memory capabilities. ")
    react_agent_executor = create_react_agent(
        model=chat_model,
        tools = [],
        prompt=SystemMessage(prompt_content),
    )
    
    def call_model_node(state):
        return call_model(state, react_agent_executor)
    
    def summarize_conversation_node(state):
        return summarize_conversation(state, chat_model)
    
    workflow = StateGraph(State)
    workflow.add_node("conversation", call_model_node)
    workflow.add_node("summarize_conversation", summarize_conversation_node)
    workflow.add_edge(START, "conversation")
    workflow.add_conditional_edges("conversation", should_continue)
    workflow.add_edge("summarize_conversation", END)
    
    checkpointer = SqliteSaver(conn=conn)
    app = workflow.compile(checkpointer=checkpointer)
    
    return app, checkpointer

#↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑ Graph Definition ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
