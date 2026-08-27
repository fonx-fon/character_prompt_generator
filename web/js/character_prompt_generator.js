import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

async function fetchModels(url) {
    const resp = await api.fetchApi(
        `/character_prompt_generator/models?url=${encodeURIComponent(url)}`
    );
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || resp.statusText);
    return data.models;
}

function notifyError(message) {
    const toast = app.extensionManager?.toast;
    if (toast?.add) {
        toast.add({ severity: "error", summary: "Character Prompt Generator", detail: message, life: 5000 });
    } else {
        alert(message);
    }
}

app.registerExtension({
    name: "CharacterPromptGenerator.Connection",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "CPG_LLMConnection") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);

            const urlWidget = this.widgets.find((w) => w.name === "url");
            const modelWidget = this.widgets.find((w) => w.name === "model");

            const refresh = async (showError) => {
                try {
                    const models = await fetchModels(urlWidget.value);
                    modelWidget.options.values = models;
                    // 保存済みワークフローの値は温存し、未選択のときだけ先頭を選ぶ
                    if (models.length && !models.includes(modelWidget.value)) {
                        if (!modelWidget.value) modelWidget.value = models[0];
                    }
                    this.setDirtyCanvas(true, false);
                } catch (e) {
                    if (showError) notifyError(`Failed to fetch model list: ${e.message}`);
                }
            };

            this.addWidget("button", "🔄 Refresh models", null, () => refresh(true));
            this.addWidget("button", "⏏ Unload model", null, async () => {
                try {
                    const resp = await api.fetchApi("/character_prompt_generator/unload", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ url: urlWidget.value, model: modelWidget.value }),
                    });
                    const data = await resp.json();
                    if (!resp.ok) throw new Error(data.error || resp.statusText);
                } catch (e) {
                    notifyError(`Failed to unload model: ${e.message}`);
                }
            });

            refresh(false);
        };
    },
});
