import gradio as gr
import requests
import time
import json
from contextlib import closing
from websocket import create_connection
from deep_translator import GoogleTranslator
from langdetect import detect
import os
from PIL import Image
import io
import base64


def flip_text(prompt, negative_prompt, task, steps, sampler, cfg_scale, seed):
    result = {"prompt": prompt,"negative_prompt": negative_prompt,"task": task,"steps": steps,"sampler": sampler,"cfg_scale": cfg_scale,"seed": seed}
    print(result)

    import urllib3
    http = urllib3.PoolManager()
    response = http.request('GET', 'https://www.gennomis.com')

    
    print("-->>>", response.text)
    generation_data = {
        'model_id': '21312',
        'prompt': prompt,
        'use_default_neg': 'false',
        'width': '512',
        'height': '512',
        'negative_prompt': request.negative_prompt,
        'num_images': '1',
        'nsfwMode': 'true',
    }
    

    # Настройка заголовков
    headers = {
        'origin': 'https://www.gennomis.com',
        'content-type': 'application/x-www-form-urlencoded'
    }

    # Отправка запроса на генерацию
    response = requests.post(
        url='https://www.gennomis.com/api/generate',
        headers=headers,
        data=generation_data
    )

    # Извлечение URL сгенерированного изображения
    generated_image = response.json()['images'][0]
    
    return {"response": generated_image}


def mirror(image_output, scale_by, method, gfpgan, codeformer):

    url_up = os.getenv("url_up")
    url_up_f = os.getenv("url_up_f")

    scale_by = int(scale_by)
    gfpgan = int(gfpgan)
    codeformer = int(codeformer)
    
    with open(image_output, "rb") as image_file:
        encoded_string2 = base64.b64encode(image_file.read())
        encoded_string2 = str(encoded_string2).replace("b'", '')

    encoded_string2 = "data:image/png;base64," + encoded_string2
    data = {"fn_index":81,"data":[0,0,encoded_string2,None,"","",True,gfpgan,codeformer,0,scale_by,512,512,None,method,"None",1,False,[],"",""],"session_hash":""}
    # print(data)
    r = requests.post(f"{url_up}", json=data, timeout=100)
    # print(r.text)
    ph = f"{url_up_f}" + str(r.json()['data'][0][0]['name'])
    return ph

css = """
.gradio-container {
min-width: 100% !important;
padding: 0px !important;
}
#generate {
    width: 100%;
    background: #e253dd !important;
    border: none;
    border-radius: 50px;
    outline: none !important;
    color: white;
}
#generate:hover {
    background: #de6bda !important;
    outline: none !important;
    color: #fff;
    }
#image_output {
display: flex;
justify-content: center;
}
footer {visibility: hidden !important;}
#image_output {
height: 100% !important;
}
"""

with gr.Blocks(css=css) as demo:

    with gr.Tab("Базовые настройки"):
        with gr.Row():
            prompt = gr.Textbox(placeholder="Введите описание изображения...", show_label=True, label='Описание изображения:', lines=3)
        with gr.Row():
            task = gr.Radio(interactive=True, value="Deliberate 3", show_label=True, label="Модель нейросети:", 
                            choices=["AbsoluteReality 1.8.1", "Elldreth's Vivid Mix", "Anything V5", "Openjourney V4", "Analog Diffusion", 
                                     "Lyriel 1.6", "Realistic Vision 5.0", "Dreamshaper 8", "epiCRealism v5", 
                                     "CyberRealistic 3.3", "ToonYou 6", "Deliberate 3"])
    with gr.Tab("Расширенные настройки"):
        with gr.Row():
            negative_prompt = gr.Textbox(placeholder="Negative Prompt", show_label=True, label='Negative Prompt:', lines=3, value="[deformed | disfigured], poorly drawn, [bad : wrong] anatomy, [extra | missing | floating | disconnected] limb, (mutated hands and fingers), blurry")
        with gr.Row():
            sampler = gr.Dropdown(value="DPM++ SDE Karras", show_label=True, label="Sampling Method:", choices=[
                "Euler", "Euler a", "Heun", "DPM++ 2M Karras", "DPM++ SDE Karras", "DDIM"])
        with gr.Row():
            steps = gr.Slider(show_label=True, label="Sampling Steps:", minimum=1, maximum=30, value=25, step=1)
        with gr.Row():
            cfg_scale = gr.Slider(show_label=True, label="CFG Scale:", minimum=1, maximum=20, value=7, step=1)
        with gr.Row():
            seed = gr.Number(show_label=True, label="Seed:", minimum=-1, maximum=1000000, value=-1, step=1)

    with gr.Tab("Настройки апскейлинга"):
        with gr.Column():
            with gr.Row():
                scale_by = gr.Number(show_label=True, label="Во сколько раз увеличить:", minimum=1, maximum=4, value=2, step=1)
            with gr.Row():
                method = gr.Dropdown(show_label=True, value="ESRGAN_4x", label="Алгоритм увеличения", choices=["ScuNET GAN", "SwinIR 4x", "ESRGAN_4x", "R-ESRGAN 4x+", "R-ESRGAN 4x+ Anime6B"])
        with gr.Column():
            with gr.Row():
                gfpgan = gr.Slider(show_label=True, label="Эффект GFPGAN (для улучшения лица)", minimum=0, maximum=1, value=0, step=0.1)
            with gr.Row():
                codeformer = gr.Slider(show_label=True, label="Эффект CodeFormer (для улучшения лица)", minimum=0, maximum=1, value=0, step=0.1)

    
    with gr.Column():
        text_button = gr.Button("Сгенерировать изображение", variant='primary', elem_id="generate")
    with gr.Column():
        image_output = gr.Image(show_label=True, show_download_button=True, interactive=False, label='Результат:', elem_id='image_output', type='filepath')
        text_button.click(flip_text, inputs=[prompt, negative_prompt, task, steps, sampler, cfg_scale, seed], outputs=image_output)

        img2img_b = gr.Button("Увеличить изображение", variant='secondary')
        image_i2i = gr.Image(show_label=True, label='Увеличенное изображение:')
        img2img_b.click(mirror, inputs=[image_output, scale_by, method, gfpgan, codeformer], outputs=image_i2i)
        
        
demo.queue(default_concurrency_limit=24)
demo.launch()
