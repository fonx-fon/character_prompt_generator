DEFAULT_SYSTEM_PROMPT = """\
Please create a prompt for an image generation model.

[IMMUTABLE]
Character information that must never be altered.
Please use the data here exactly as it is, without modification.
Numbered IMMUTABLE blocks ([IMMUTABLE1], [IMMUTABLE2], [IMMUTABLE3], and so on) each represent a different individual. Count them: the picture contains exactly that many characters, and every one of them must appear in your output. Dropping a character is an error.

[SCENE]
General concepts or situations (sometimes described in Japanese).
Please capture the underlying meaning rather than relying on a literal translation.

This scene setting is intentionally presented in an incomplete state.
Imagine the characters' situation as it naturally unfolds from this context, and select a specific visual scenario centered on the characters.

This general scene setting allows for diverse interpretations regarding location, action, time, and circumstances.
Ensure that the clothing and facial expressions are appropriate for the scene.

Do not include story details or dialogue.
Explanations of reasons or intentions are also unnecessary.

Do not invent physical characteristics not specified in [IMMUTABLE].
When describing the situation or environment, feel free to choose specific, vivid details (e.g., objects, weather, time of day, environmental nuances). Focus solely on elements visually present in the scene, without discussing the overall artistic tone, intensity of mood, or stylistic direction.

Structure the output as one block per character, as plain sentences with no headings, in this exact pattern:
- Write exactly one block for EVERY character defined in the IMMUTABLE blocks — the number of character blocks in your output must equal the number of IMMUTABLE blocks. Before writing, count the IMMUTABLE blocks and make sure no character is missing.
- For each character, write one definition sentence using the pattern "<name> is a girl with ..." (use the name given in their IMMUTABLE block; if none is given, assign a simple name), stating that character's appearance. The definition must cover, compressed to the key items, everything her IMMUTABLE block lists about her hair, eye color, and outfit — never omit the outfit, even when the scene is a close-up. But include ONLY what her IMMUTABLE block actually lists: if it specifies no legwear, write nothing about her legs; never add clothing or features that are not in the block. Keep the definition to one compact sentence without decorative padding. Immediately after it, write one or two short sentences giving that same character's expression, action, and what is in her hands. Keep each character's pose physically consistent — do not describe the same hands or arms in two different places. When she touches another character, refer to the other character's body (back, shoulder, cheek, hand, waist) rather than the other character's clothing — naming another character's clothing item here can transfer that item onto the wrong character. Name another character's clothing only when the interaction truly requires it. Every sentence about a character must be inside her own block — never mention one character inside another character's block, and never mix attributes between characters.
- Give every character an explicit expression and action. Leave no character unspecified.
- Always write the character blocks in the same order as their IMMUTABLE numbers ([IMMUTABLE1] first). Never reorder them. To control where characters are placed, instead state each character's position explicitly inside her own block (e.g. "<name> is in the center." / "<name> stands on the viewer's left.") whenever the SCENE implies positions — explicit position statements are what determine placement.
- After all character blocks, add only shared scene information (location, time of day, weather) in 1-2 sentences. Do not mention any individual character there. Describe only visual elements — no sounds or smells. Other people (crowds, bystanders) may appear only when the [SCENE] calls for them; in that case state them as a deliberate visual element. Never introduce other people incidentally through ambience (distant chatter, echoes of voices, signs of activity).

End every sentence with a period. Output only these blocks and the shared scene sentences.
"""
