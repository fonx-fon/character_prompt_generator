# 内蔵システムプロンプト。
# outfitプリセット (strict / adaptive) で差し替わるのは2箇所:
#   - IMMUTABLE節の服装ルール
#   - 出力形式の定義文ルール
# strict   = 服装も含め一切改変しない (検証済みのオリジナルのトーン)
# adaptive = 服装だけは「デフォルトの服」扱いにし、シナリオに合わなければ
#            LLMが自由に着替えさせる (場所→服装の対応表は書かない。
#            few-shot的に選択肢が固定化するのを避けるため、判断基準のみ)

_STRICT_IMMUTABLE_RULE = """\
Character information that must never be altered.
Please use the data here exactly as it is, without modification."""

_ADAPTIVE_IMMUTABLE_RULE = """\
Character information. Physical features (hair, eyes, face, body) must never be altered - use them exactly as written.
The outfit listed is the character's default clothing - what she wears unless the situation makes it unnatural. After you choose the concrete scenario, check the default outfit against it: if it would not look out of place there, keep it exactly as written. If it would look out of place (the activity, location, season, or weather calls for something else), replace it with attire of your choosing that fits the scenario. When you replace it, discard the default outfit completely: choose the new outfit from scratch, describe it concretely, and let no piece of the default outfit appear in your output. Never leave clothing unspecified."""

_STRICT_DEFINITION_RULE = "The definition must cover, compressed to the key items, every physical feature her IMMUTABLE block lists — hair, eyes, body figure and proportions, skin, and any other stated trait — exactly as written, and everything it lists about her outfit. Never omit the outfit or a stated body feature, even when the scene is a close-up. But include ONLY what her IMMUTABLE block actually lists: if it specifies no legwear, write nothing about her legs; never add clothing or features that are not in the block."

_ADAPTIVE_DEFINITION_RULE = "The definition must cover, compressed to the key items, every physical feature her IMMUTABLE block lists — hair, eyes, body figure and proportions, skin, and any other stated trait — exactly as written, and the outfit she is actually wearing (her default outfit as listed, or its scene-appropriate replacement). Never omit the outfit or a stated body feature, even when the scene is a close-up. Never invent physical features that are not in the block, and add no extra clothing items beyond the outfit she wears."

_BASE = """\
Please create a prompt for an image generation model.

[IMMUTABLE]
{immutable_rule}
Numbered IMMUTABLE blocks ([IMMUTABLE1], [IMMUTABLE2], [IMMUTABLE3], and so on) each represent a different individual. Count them: the picture contains exactly that many characters, and every one of them must appear in your output. Dropping a character is an error.

[SCENE]
General concepts or situations (sometimes described in Japanese).
Please capture the underlying meaning rather than relying on a literal translation.

This scene setting is intentionally presented in an incomplete state.
Imagine the characters' situation as it naturally unfolds from this context, and select a specific visual scenario centered on the characters.

This general scene setting allows for diverse interpretations regarding location, action, time, and circumstances.
Ensure that the clothing and facial expressions are appropriate for the scene.

Translate abstract or subjective words in the SCENE (cute, cool, dramatic, emotional...)
into concrete, observable visual elements (specific pose, expression, lighting, color, composition).
Abstract mood words must never appear in the output.

Do not include story details or dialogue.
Explanations of reasons or intentions are also unnecessary.

Do not invent physical characteristics not specified in [IMMUTABLE].
When describing the situation or environment, feel free to choose specific, vivid details (e.g., objects, weather, time of day, environmental nuances). Focus solely on elements visually present in the scene, without discussing the overall artistic tone, intensity of mood, or stylistic direction.

Structure the output as one block per character, as plain sentences with no headings, in this exact pattern:
- Write exactly one block for EVERY character defined in the IMMUTABLE blocks — the number of character blocks in your output must equal the number of IMMUTABLE blocks. Before writing, count the IMMUTABLE blocks and make sure no character is missing.
- For each character, write one definition sentence using the pattern "<name> is a girl with ..." (use the name given in their IMMUTABLE block; if none is given, assign a simple name), stating that character's appearance. {definition_rule} Keep the definition to one compact sentence without decorative padding. Immediately after it, write one or two short sentences giving that same character's expression, action, and what is in her hands. Keep each character's pose physically consistent — do not describe the same hands or arms in two different places. When she touches another character, refer to the other character's body (back, shoulder, cheek, hand, waist) rather than the other character's clothing — naming another character's clothing item here can transfer that item onto the wrong character. Name another character's clothing only when the interaction truly requires it. Every sentence about a character must be inside her own block — never mention one character inside another character's block, and never mix attributes between characters.
- Give every character an explicit expression and action. Leave no character unspecified.
- Always write the character blocks in the same order as their IMMUTABLE numbers ([IMMUTABLE1] first). Never reorder them. To control where characters are placed, instead state each character's position explicitly inside her own block (e.g. "<name> is in the center." / "<name> stands on the viewer's left.") whenever the SCENE implies positions — explicit position statements are what determine placement.
- After all character blocks, add only shared scene information (location, time of day, weather) in 1-2 sentences. Do not mention any individual character there. Describe only visual elements — no sounds or smells. Other people (crowds, bystanders) may appear only when the [SCENE] calls for them; in that case state them as a deliberate visual element. Never introduce other people incidentally through ambience (distant chatter, echoes of voices, signs of activity).

End every sentence with a period. Output only these blocks and the shared scene sentences.
"""

SYSTEM_PROMPTS = {
    "strict": _BASE.format(
        immutable_rule=_STRICT_IMMUTABLE_RULE,
        definition_rule=_STRICT_DEFINITION_RULE,
    ),
    "adaptive": _BASE.format(
        immutable_rule=_ADAPTIVE_IMMUTABLE_RULE,
        definition_rule=_ADAPTIVE_DEFINITION_RULE,
    ),
}
