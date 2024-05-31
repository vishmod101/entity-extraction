import streamlit as st


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def remote_css(url):
    st.markdown(f'<link href="{url}" rel="stylesheet">', unsafe_allow_html=True)


def icon(icon_name):
    st.markdown(f'<i class="material-icons">{icon_name}</i>', unsafe_allow_html=True)


class stNotification:
    """
    This is the custom notification
    """
    def build_style(self):
        "Getting theme colors"
        pc = st.get_option('theme.primaryColor')
        bc = st.get_option('theme.backgroundColor')
        sbc = st.get_option('theme.secondaryBackgroundColor')
        tc = st.get_option('theme.textColor')
        return {'pc': pc, "bc": bc, "sbc": sbc, "tc": tc}

    def __init__(self, text, spinner=False):
        "Getting default theme and building style"
        styles = self.build_style()

        loader = '<br>'

        "Building notification object"
        self.notification = f'''
            <div class="custom-notification" style="font-size:0.8rem;min-width:40%;max-width:62%;top:0rem;background-color: {styles["bc"]};padding: 0.5rem;position: fixed;line-height: 2rem;text-align: center;border-style: solid;border-width: 2px;border-image: linear-gradient(-90deg,{styles['bc']}, {styles['pc']}) 1;border-top-width:0px;border-right-width:0px;">
                <div style="display: flex;flex-wrap: nowrap;">
                    {loader}
                    <div style="margin-left:1rem;">
                        {text}
                    </div>
                </div>
            </div>
            '''

    def __enter__(self):
        self.notification_object = st.markdown(
            self.notification, unsafe_allow_html=True)

    def __exit__(self, *args, **kwargs):
        self.notification_object.empty()


def set_page_title(title):
    st.sidebar.markdown(f'<p class="title">{title}</p>', unsafe_allow_html = True)


def set_loggedin_user(name):
    st.markdown(f'<p class="title">{name}</p>', unsafe_allow_html = True)

