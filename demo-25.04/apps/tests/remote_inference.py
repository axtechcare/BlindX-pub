# MIT License (c) 2024, 2025 Masakazu Suzuoki, AxTecChare
# See LICENSE.txt for details.

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from blindx.remote_inference import RemoteInference

import blindx.misc as misc
import asyncio

misc.set_logger(__file__)
async def main():

    input_text = (
        "「きみのひとみにこいしてる」（げんだい`Cant' take my eyes off you`）はふらんきー・ゔぁりのさくひんで"
        "のちにぼーいず・たうん・ぎゃんぐがかばーしにほんでは１９８２ねんに"
        "おりこんようがくしんぐるちゃーとで３しゅうれんぞく１いをきろくしました。"
    )
    fixed_text = '「君の瞳に'
    aux_args = 'early_stopping=True,return_legacy_cache=False'
    async with RemoteInference() as inference:
        result = await inference.send_recv_async('T0:8:', input_text, fixed_text, aux_args)
        print(result.replace(':', '\n'))


asyncio.run(main())
