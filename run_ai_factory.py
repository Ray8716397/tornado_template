import argparse
import base64
import json
import os
import sys

import cv2
import pika
from utils.singleton_config import config

if __name__ == "__main__":
    # params for prediction engine
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", type=str, default=config["ocr"]["lang"])
    params = parser.parse_args()
    # feat
    mq_name = config["mq_name"] if "mq_name" in config.keys() and config["mq_name"] != '' else 'ocr_queue'

    def on_request(ch, method, props, body):
        # 图片路径
        img_path = str(body.decode())
        if os.path.exists(img_path):
            upload_dp = os.path.dirname(img_path)
            fn = os.path.basename(img_path)
            user_storage_dp = os.path.dirname(upload_dp)
            server_results_dp = os.path.join(user_storage_dp, 'server_results')
            inference_results_dp = os.path.join(user_storage_dp, 'inference_results')
            img_type = fn.split('.')[-1]

            # predict
            str_results = os.popen(
                f'cd {config["ocr"]["work_dir"]} && {sys.executable} lib/ocr/deploy/hubserving/ocr_system/module.py --image_path="{img_path}" --lang={params.lang} --server_results_dp={server_results_dp} --inference_results_dp={inference_results_dp}').readlines()[-1].replace("'", '"')

            # json
            json_result = json.loads(str_results)

            # response
            draw_img = cv2.imread(os.path.join(inference_results_dp, fn))

            img_bytes = cv2.imencode(f".{img_type}", draw_img[:, :, ::-1])[1]
            response = json.dumps(
                {'res_img': base64.b64encode(img_bytes.tobytes()).decode('utf8'), 'json_result': json_result})
        else:
            response = ''

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)


    # pika
    auth = pika.PlainCredentials('guest', 'guest')
    connection = pika.BlockingConnection(pika.ConnectionParameters('0.0.0.0', 5672, '/', auth))
    channel = connection.channel()

    channel.queue_declare(queue=mq_name)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=mq_name, on_message_callback=on_request)

    print(" [x] Awaiting RPC requests")
    channel.start_consuming()
