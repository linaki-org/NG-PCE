"""Little tool to quickly generate voices using ElevenLabs for game texts using a specific lang file"""
import os
import yaml

def voiceify_patch(language):
    try:
        import elevenlabs
    except ImportError:
        print("ElevenLabs python SDK is not installed, do you want to install it ?")
        answer=input("Y/n : ").lower()
        if answer != "n":
            import pip
            pip.main(["install", "elevenlabs"])
        else:
            return

    from elevenlabs.client import ElevenLabs
    from elevenlabs import save

    if "ELEVENLABS_API_KEY" in os.environ:
        api_key=os.environ["ELEVENLABS_API_KEY"]
        print("Using environment ElevenLabs API Key")
    else:
        api_key=input("Please enter your ElevenLabs API Key :")
        api_key="sk_0506ed7d71e1fb70dcd2b9079ace51ac4cc18d95ac1ebaa5"
        if not api_key:
            print("Please provide an API key")
            return
        os.environ["ELEVENLABS_API_KEY"]=api_key
    voice_id=input("Please enter the id of the voice you want to use :")
    if not voice_id:
        print("No voice id entered, defaulting to Harry")
        voice_id="SOYHLrjzK2X1ezoPC6cr"

    elevenlabs = ElevenLabs(api_key=api_key)
    with open(f"lang/{language}.yaml", encoding="utf-8") as f:
        lang_patch=yaml.safe_load(f)
    language_name=lang_patch["language_name"]

    print(f"Retrieving texts to voiceify in {language_name}...")
    texts={"cannot_do" : lang_patch["system_messages"]["CANNOT_DO"],
         "cannot_reach" : lang_patch["system_messages"]["CANNOT_REACH"],
         "does_not_work" : lang_patch["system_messages"]["DOES_NOT_WORK"],
         "makes_no_sense" : lang_patch["system_messages"]["MAKES_NO_SENSE"],
         "default_look" : lang_patch["system_messages"]["DEFAULT_LOOK"],
         "picked_up" : lang_patch["system_messages"]["PICKED_UP"]}

    for description_key in lang_patch["descriptions"]:
        description_txt=lang_patch["descriptions"][description_key]
        texts[description_key]=description_txt

    for key in texts:
        text=texts[key]
        print(f"Generating voice for {key} ('{text}')")
        audio = elevenlabs.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_v3",
            output_format="opus_48000_64",
        )

        with open(f"voice/{language}/{key}.ogg", "wb") as f:
            for chunk in audio:
                f.write(chunk)