from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .chains import generate_answer
from .models import Conversation, Message, MessagePhoto
from .retrieval import retrieve_photos


@login_required
def conversation(request, pk=None):
    if pk is None:
        conv = Conversation.objects.filter(user=request.user).first()
        if conv is None:
            conv = Conversation.objects.create(user=request.user)
        return redirect("chat:conversation", pk=conv.pk)

    conv = get_object_or_404(Conversation, pk=pk, user=request.user)
    # Named "chat_messages", not "messages" -- that name collides with the
    # django.contrib.messages flash-message context variable used in base.html.
    chat_messages = conv.messages.prefetch_related("message_photos__photo")
    return render(request, "chat/conversation.html", {"conversation": conv, "chat_messages": chat_messages})


@login_required
@require_http_methods(["POST"])
def send_message(request, pk):
    conv = get_object_or_404(Conversation, pk=pk, user=request.user)
    query = request.POST.get("content", "").strip()
    if not query:
        return render(request, "chat/_message_pair.html", {})

    user_message = Message.objects.create(conversation=conv, role=Message.Role.USER, content=query)

    try:
        results = list(retrieve_photos(request.user, query))
        answer = generate_answer(query, results)
    except Exception:
        results = []
        answer = "Sorry, I couldn't search your photos just now. Check that OPENAI_API_KEY is set and try again."

    assistant_message = Message.objects.create(conversation=conv, role=Message.Role.ASSISTANT, content=answer)

    if results:
        MessagePhoto.objects.bulk_create(
            [
                MessagePhoto(message=assistant_message, photo=photo, rank=i, distance=getattr(photo, "distance", None))
                for i, photo in enumerate(results)
            ]
        )

    return render(
        request,
        "chat/_message_pair.html",
        {"user_message": user_message, "assistant_message": assistant_message},
    )
