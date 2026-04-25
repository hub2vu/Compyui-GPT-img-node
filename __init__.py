from .gpt_img_node import (
    GPTImgAPIEdit,
    GPTImgAPIGenerate,
    GPTImgAPIGenerateAdvanced,
    GPTImgOAuthEdit,
    GPTImgOAuthGenerate,
    GPTImgOAuthGenerateAdvanced,
)


NODE_CLASS_MAPPINGS = {
    "GPTImgOAuthGenerate": GPTImgOAuthGenerate,
    "GPTImgOAuthGenerateAdvanced": GPTImgOAuthGenerateAdvanced,
    "GPTImgOAuthEdit": GPTImgOAuthEdit,
    "GPTImgAPIGenerate": GPTImgAPIGenerate,
    "GPTImgAPIGenerateAdvanced": GPTImgAPIGenerateAdvanced,
    "GPTImgAPIEdit": GPTImgAPIEdit,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GPTImgOAuthGenerate": "GPT img OAuth Generate",
    "GPTImgOAuthGenerateAdvanced": "GPT img OAuth Generate Advanced",
    "GPTImgOAuthEdit": "GPT img OAuth Edit",
    "GPTImgAPIGenerate": "GPT img API Generate",
    "GPTImgAPIGenerateAdvanced": "GPT img API Generate Advanced",
    "GPTImgAPIEdit": "GPT img API Edit",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
