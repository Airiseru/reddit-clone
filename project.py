from __future__ import annotations
from flet.auth.authorization import Authorization
from flet.auth.oauth_provider import OAuthProvider
import flet as ft
import aiohttp
import base64
import time
import os

client_id = os.environ['CLIENT_ID']
client_secret = ""
base_auth_url = "https://www.reddit.com"
authorization_endpoint = f"{base_auth_url}/api/v1/authorize.compact?duration=permanent"
token_endpoint = f"{base_auth_url}/api/v1/access_token"
redirect_url = "https://cs12222project-dee-denise.onrender.com/api/oauth/redirect"
user_scopes = ['identity', 'read', 'vote']

class MyAuthorization(Authorization):
    def __init__ (self, *args, **kwargs):
        super(MyAuthorization, self).__init__(*args, **kwargs)

    def _Authorization__get_default_headers(self):
        username = client_id
        encoded = base64.b64encode(f'{username}:'.encode('utf8')).decode('utf8')

        return {"User-Agent": f"Flet/0.6.2", "Authorization": f"Basic {encoded}", }

async def main(page: ft.Page):
    provider = OAuthProvider(client_id, client_secret, authorization_endpoint, token_endpoint, redirect_url, user_scopes=user_scopes)
    access_token = ""
    post_dict = {}
    recently_opened_post = ""

    async def login_button_click(e):
        await page.login_async(provider, authorization=MyAuthorization)

    async def on_login(e: ft.LoginEvent):
        if not e.error:
            access_token = page.auth.token.access_token
            await display(access_token)

    async def logout_button_click(e):
        await page.clean_async()
        await starting_screen()

    async def on_logout(e):
        await toggle_login_buttons()
    
    async def toggle_login_buttons():
        login_button.visible = page.auth is None
        logout_button.visible = page.auth is not None
        await page.update_async()

    login_button = ft.ElevatedButton("Login", on_click=login_button_click, icon="login_rounded")
    logout_button = ft.ElevatedButton("Logout", on_click=logout_button_click, icon="logout_rounded")

    # Starting Screen - Not Logged In
    async def starting_screen():
        await page.clean_async()
        page.appbar = ft.AppBar(
            title=ft.Container(content=ft.Row([ft.Icon(name=ft.icons.REDDIT, color="#FF5700", size=35), ft.Text("CS12 - Dee", color=ft.colors.BLACK)])),
            bgcolor="#fffff4",
        )
        base_url_text = ft.TextField(label="Base Auth URL", value=f"{base_auth_url}")
        base_api_text = ft.TextField(label="Base API URL", value="https://oauth.reddit.com")

        await page.add_async(ft.Divider(color=ft.colors.TRANSPARENT))
        await page.add_async(base_url_text)
        await page.add_async(base_api_text)
        
        page.on_login = on_login
        await page.add_async(login_button)

    # Function for refresh button
    async def refresh_click(e):
        await page.clean_async()
        await display(access_token)

    refresh_button = ft.IconButton(icon=ft.icons.REFRESH, on_click=refresh_click, icon_color=ft.colors.GREY_900)

    # To check if button should be colored or not
    async def toggle_vote_buttons(votation, up_btn, down_btn, score_text):
        if votation is True:
            up_btn.icon_color=ft.colors.ORANGE_300
            down_btn.icon_color=ft.colors.WHITE
            score_text.color=ft.colors.ORANGE_300
        elif votation is False:
            up_btn.icon_color=ft.colors.WHITE
            down_btn.icon_color=ft.colors.BLUE_300
            score_text.color=ft.colors.BLUE_300
        elif votation is None:
            up_btn.icon_color=ft.colors.WHITE
            down_btn.icon_color=ft.colors.WHITE
            score_text.color=ft.colors.WHITE
        await page.update_async()

    # Main Display - After Logging In
    async def display(access_token):
        await page.clean_async()
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        after_post_id = ""

        page.appbar = ft.AppBar(
            title=ft.Container(content=ft.Row([ft.Icon(name=ft.icons.REDDIT, color="#FF5700", size=35), ft.Text("CS12 - Dee", color=ft.colors.BLACK)])),
            bgcolor="#fffff4",
            actions=[refresh_button, logout_button]
        )

        page.on_logout = on_logout
        # List View for the posts
        list_view = ft.ListView(expand=1, spacing=10, padding=20)

        async def load_more_click(e):
            await load_posts(list_view)
            await page.update_async()

        # Function to update the upvote color, score, and reflect in Reddit
        async def update_upvote(post_id):
            up_btn = post_dict[post_id]["upvote"]
            down_btn = post_dict[post_id]["downvote"]
            post_likes = post_dict[post_id]["score"]
            show_score = post_dict[post_id]["score-text"]
            post_dict[post_id]["user-vote"] = True
            dir = 1

            # Not upvoted or downvoted
            if up_btn.icon_color == ft.colors.WHITE and down_btn.icon_color != ft.colors.BLUE_300:
                up_btn.icon_color = ft.colors.ORANGE_300
                post_dict[post_id]["score"] = post_likes + 1
                show_score.value = post_dict[post_id]["score"]
                show_score.color = ft.colors.ORANGE_300
            # Was upvoted
            elif up_btn.icon_color == ft.colors.ORANGE_300:
                up_btn.icon_color = ft.colors.WHITE
                dir = 0
                post_dict[post_id]["score"] = post_likes - 1
                show_score.value = post_dict[post_id]["score"]
                post_dict[post_id]["user-vote"] = None
                show_score.color = ft.colors.WHITE
            # Was downvoted
            else:
                up_btn.icon_color = ft.colors.ORANGE_300
                down_btn.icon_color = ft.colors.WHITE
                post_dict[post_id]["score"] = post_likes + 2
                show_score.value = post_dict[post_id]["score"]
                show_score.color = ft.colors.ORANGE_300

            post_request = aiohttp.request(method='post', url="https://oauth.reddit.com/api/vote", data={'dir': dir, 'id': post_id}, headers=headers)

            async with post_request as req:
                pass

            await page.update_async()

        # Function to update the downvote color, score, and reflect in Reddit
        async def update_downvote(post_id):
            up_btn = post_dict[post_id]["upvote"]
            down_btn = post_dict[post_id]["downvote"]
            post_likes = post_dict[post_id]["score"]
            show_score = post_dict[post_id]["score-text"]
            post_dict[post_id]["user-vote"] = False
            dir = -1

            # Not upvoted or downvoted
            if down_btn.icon_color == ft.colors.WHITE and up_btn.icon_color != ft.colors.ORANGE_300:
                down_btn.icon_color = ft.colors.BLUE_300
                post_dict[post_id]["score"] = post_likes - 1
                show_score.value = post_dict[post_id]["score"]
                show_score.color = ft.colors.BLUE_300
            # Was downvoted
            elif down_btn.icon_color == ft.colors.BLUE_300:
                down_btn.icon_color = ft.colors.WHITE
                dir = 0
                post_dict[post_id]["score"] = post_likes + 1
                show_score.value = post_dict[post_id]["score"]
                post_dict[post_id]["user-vote"] = None
                show_score.color = ft.colors.WHITE
            # Was upvoted
            else:
                up_btn.icon_color = ft.colors.WHITE
                down_btn.icon_color = ft.colors.BLUE_300
                post_dict[post_id]["score"] = post_likes - 2
                show_score.value = post_dict[post_id]["score"]
                show_score.color = ft.colors.BLUE_300

            post_request = aiohttp.request(method='post', url="https://oauth.reddit.com/api/vote", data={'dir': dir, 'id': post_id}, headers=headers)

            async with post_request as req:
                pass

            await page.update_async()
        
        # Function for list view posts
        async def load_posts(lv):
            nonlocal after_post_id
            nonlocal post_dict

            if after_post_id == "":
                request = aiohttp.request(method='get', url="https://oauth.reddit.com/new.json", headers=headers)
            else:
                request = aiohttp.request(method='get', url=f"https://oauth.reddit.com/new.json?after={after_post_id}", headers=headers)

            async with request as resp:
                info = await resp.json()
                posts = info['data']['children']
                after_post_id = info['data']['after']

            for post in posts:
                data = post["data"]

                # Upvote button with reference to the post
                async def make_upvote_btn(post_id):
                    async def update_upvote_click(e):
                        await update_upvote(post_id)
                        await page.update_async()
                    
                    return ft.IconButton(icon="arrow_upward", icon_color=ft.colors.WHITE, on_click=update_upvote_click)
                
                # Downvote button with reference to the post
                async def make_downvote_btn(post_id):
                    async def update_downvote_click(e):
                        await update_downvote(post_id)
                        await page.update_async()
                    
                    return ft.IconButton(icon="arrow_downward", icon_color=ft.colors.WHITE, on_click=update_downvote_click)
                
                async def make_post(post_id):
                    async def open_post_click(e):
                        await page.clean_async()
                        nonlocal recently_opened_post
                        recently_opened_post = post_id
                        await open_post(post_id, access_token)
                        await page.update_async()
                    
                    return ft.Container(
                        margin=10,
                        padding=10,
                        content=ft.Row(
                            [
                                ft.Container(content=ft.Column([upvote_button, ft.Container(content=score), downvote_button], horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=100, spacing=0), alignment=ft.alignment.center),

                                ft.Container(content=ft.Column([ft.Row([ft.Text(data["subreddit_name_prefixed"], weight=ft.FontWeight.W_900), ft.Text(data["author"], color=ft.colors.GREY_400)]), ft.Container(content=ft.Text(data["title"], max_lines=5, size=17), width=1400), ft.Container(content=ft.Row([ft.Icon(name=ft.icons.CHAT_BUBBLE_OUTLINE_OUTLINED, color=ft.colors.GREY_400, size=20), ft.Text(f"{data['num_comments']} comments", color=ft.colors.GREY_400, size=15)], vertical_alignment=ft.CrossAxisAlignment.CENTER))]), on_click=open_post_click)
                            ]
                        )
                    )
                
                upvote_button = await make_upvote_btn(data["name"])
                downvote_button = await make_downvote_btn(data["name"])
                score = ft.Text(data["score"], color=ft.colors.WHITE)
                await toggle_vote_buttons(data["likes"], upvote_button, downvote_button, score)

                await page.update_async()

                # Add each post with their corresponding id, upvote, downvote, and score into a dict
                post_dict[data["name"]] = {"upvote": upvote_button, "downvote": downvote_button, "score": data["score"], "score-text": score, "user-vote": data["likes"]}

                single_post = ft.Card(
                    color=ft.colors.GREY_900,
                    content=await make_post(data["name"])
                )

                lv.controls.append(single_post)
            
            await page.add_async(lv)

            load_more_btn = ft.Container(content=ft.ElevatedButton(width=400,  on_click=load_more_click, content=ft.Text("Load more...", size=22), style=ft.ButtonStyle(padding=15)), padding=3, alignment=ft.alignment.center)
            await page.add_async(load_more_btn)
        
        await load_posts(list_view)
        await page.update_async()

    # Function to view each post
    async def open_post(post_id, access_token):
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        page.appbar = ft.AppBar(
            title=ft.Container(content=ft.Row([ft.Icon(name=ft.icons.REDDIT, color="#FF5700", size=35), ft.Text("CS12 - Dee", color=ft.colors.BLACK)])),
            bgcolor="#fffff4",
            actions=[logout_button]
        )

        view_post_url = f"https://oauth.reddit.com/comments/{post_id[3:]}.json"

        comm_request = aiohttp.request(method='get', url=view_post_url, headers=headers)

        async with comm_request as cr:
            info = await cr.json()
            post_info = info[0]["data"]["children"][0]["data"]

        async def back_click(e):
            await page.clean_async()
            await display(access_token)
            await page.update_async()

        async def refresh_post_click(e):
            await page.clean_async()
            await open_post(recently_opened_post, access_token)
            await page.update_async()

        # Container for post and comments with replies
        main_container = ft.ListView(expand=1, spacing=5)

        # Functionality buttons (back and refresh)
        back_post_btn = ft.IconButton(icon=ft.icons.ARROW_BACK_IOS_ROUNDED, tooltip="Back", icon_color=ft.colors.GREY_300, on_click=back_click)

        refresh_post_btn = ft.IconButton(icon=ft.icons.REFRESH, tooltip="Refresh post", icon_color=ft.colors.GREY_300, on_click=refresh_post_click)

        function_row = ft.Row([back_post_btn, refresh_post_btn], spacing=5)

        # Side buttons
        # Function to update the upvote color, score, and reflect in Reddit
        async def update_upvote(post_id):
            nonlocal post_info
            up_btn = up_main_btn
            down_btn = down_main_btn
            post_likes = post_info["score"]
            show_score = score_post
            post_info["likes"] = True
            dir = 1

            # Not upvoted or downvoted
            if up_btn.icon_color == ft.colors.WHITE and down_btn.icon_color != ft.colors.BLUE_300:
                up_btn.icon_color = ft.colors.ORANGE_300
                post_info["score"] = post_likes + 1
                show_score.value = post_info["score"]
                show_score.color = ft.colors.ORANGE_300
            # Was upvoted
            elif up_btn.icon_color == ft.colors.ORANGE_300:
                up_btn.icon_color = ft.colors.WHITE
                dir = 0
                post_info["score"] = post_likes - 1
                show_score.value = post_info["score"]
                post_info["likes"] = None
                show_score.color = ft.colors.WHITE
            # Was downvoted
            else:
                up_btn.icon_color = ft.colors.ORANGE_300
                down_btn.icon_color = ft.colors.WHITE
                post_info["score"] = post_likes + 2
                show_score.value = post_info["score"]
                show_score.color = ft.colors.ORANGE_300

            post_request = aiohttp.request(method='post', url="https://oauth.reddit.com/api/vote", data={'dir': dir, 'id': post_id}, headers=headers)

            async with post_request as req:
                pass

            await page.update_async()

        # Function to update the downvote color, score, and reflect in Reddit
        async def update_downvote(post_id):
            nonlocal post_info
            up_btn = up_main_btn
            down_btn = down_main_btn
            post_likes = post_info["score"]
            show_score = score_post
            post_info["likes"] = False
            dir = -1

            # Not upvoted or downvoted
            if down_btn.icon_color == ft.colors.WHITE and up_btn.icon_color != ft.colors.ORANGE_300:
                down_btn.icon_color = ft.colors.BLUE_300
                post_info["score"] = post_likes - 1
                show_score.value = post_info["score"]
                show_score.color = ft.colors.BLUE_300
            # Was downvoted
            elif down_btn.icon_color == ft.colors.BLUE_300:
                down_btn.icon_color = ft.colors.WHITE
                dir = 0
                post_info["score"] = post_likes + 1
                show_score.value = post_info["score"]
                post_info["likes"] = None
                show_score.color = ft.colors.WHITE
            # Was upvoted
            else:
                up_btn.icon_color = ft.colors.WHITE
                down_btn.icon_color = ft.colors.BLUE_300
                post_info["score"] = post_likes - 2
                show_score.value = post_info["score"]
                show_score.color = ft.colors.BLUE_300

            post_request = aiohttp.request(method='post', url="https://oauth.reddit.com/api/vote", data={'dir': dir, 'id': post_id}, headers=headers)

            async with post_request as req:
                pass

            await page.update_async()

        # Upvote button with reference to the post
        async def make_upvote_btn(post_id):
            async def update_upvote_click(e):
                await update_upvote(post_id)
                await page.update_async()
            
            return ft.IconButton(icon="arrow_upward", icon_color=ft.colors.WHITE, icon_size=17, on_click=update_upvote_click)
        
        # Downvote button with reference to the post
        async def make_downvote_btn(post_id):
            async def update_downvote_click(e):
                await update_downvote(post_id)
                await page.update_async()
            
            return ft.IconButton(icon="arrow_downward", icon_color=ft.colors.WHITE, icon_size=17, on_click=update_downvote_click)

        up_main_btn = await make_upvote_btn(post_id)
        down_main_btn = await make_downvote_btn(post_id)
        score_post = ft.Text(post_info["score"], size=14)

        await toggle_vote_buttons(post_info["likes"], up_main_btn, down_main_btn, score_post)
        await page.update_async()

        post_votes = ft.Column([up_main_btn, score_post, down_main_btn], horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=50, spacing=1)

        # Main part of the content
        post_main = ft.Column([
            ft.Row([ft.Text(post_info["subreddit_name_prefixed"], weight=ft.FontWeight.W_900), ft.Text(post_info["author"], color=ft.colors.GREY_400)]),
            ft.Container(content=ft.Text(post_info["title"], max_lines=6, size=20, weight=ft.FontWeight.W_900), width=1500),
            ft.Container(content=ft.Text(post_info["selftext"], max_lines=15, size=17), width=1500, padding=ft.padding.only(top=5, bottom=5)),
            ft.Container(content=ft.Row([ft.Icon(name=ft.icons.CHAT_BUBBLE_OUTLINE_OUTLINED, color=ft.colors.GREY_400, size=20), ft.Text(f"{post_info['num_comments']} comments", color=ft.colors.GREY_400, size=15)], vertical_alignment=ft.CrossAxisAlignment.CENTER), margin=ft.margin.only(top=20)),
            ft.Container(content=ft.Divider(color=ft.colors.SURFACE_VARIANT), width=1500, margin=ft.margin.only(top=10))
        ])

        # Putting the votes btn and main content together
        post_content = ft.Container(
            content=ft.Row([post_votes, post_main], vertical_alignment=ft.CrossAxisAlignment.START),
            margin=ft.margin.only(left=20, top=5, right=5, bottom=5),
            alignment=ft.alignment.top_left
        )

        main_container.controls.append(post_content)
        await page.update_async()

        # Comments
        comments_dict = {}

        # Function to update reddit data when upvoting a comment
        async def update_com_upvote(com_id):
            up_btn = comments_dict[com_id]["upvote"]
            down_btn = comments_dict[com_id]["downvote"]
            post_likes = comments_dict[com_id]["score"]
            show_score = comments_dict[com_id]["score-text"]
            comments_dict[com_id]["user-vote"] = True
            dir = 1

            # Not upvoted or downvoted
            if up_btn.icon_color == ft.colors.WHITE and down_btn.icon_color != ft.colors.BLUE_300:
                up_btn.icon_color = ft.colors.ORANGE_300
                comments_dict[com_id]["score"] = post_likes + 1
                show_score.value = comments_dict[com_id]["score"]
                show_score.color = ft.colors.ORANGE_300
            # Was upvoted
            elif up_btn.icon_color == ft.colors.ORANGE_300:
                up_btn.icon_color = ft.colors.WHITE
                dir = 0
                comments_dict[com_id]["score"] = post_likes - 1
                show_score.value = comments_dict[com_id]["score"]
                comments_dict[com_id]["user-vote"] = None
                show_score.color = ft.colors.WHITE
            # Was downvoted
            else:
                up_btn.icon_color = ft.colors.ORANGE_300
                down_btn.icon_color = ft.colors.WHITE
                comments_dict[com_id]["score"] = post_likes + 2
                show_score.value = comments_dict[com_id]["score"]
                show_score.color = ft.colors.ORANGE_300

            com_vote_request = aiohttp.request(method='post', url="https://oauth.reddit.com/api/vote", data={'dir': dir, 'id': com_id}, headers=headers)

            async with com_vote_request as req:
                pass

            await page.update_async()

        # Function to update reddit data when downvoting a comment
        async def update_com_downvote(com_id):
            up_btn = comments_dict[com_id]["upvote"]
            down_btn = comments_dict[com_id]["downvote"]
            post_likes = comments_dict[com_id]["score"]
            show_score = comments_dict[com_id]["score-text"]
            comments_dict[com_id]["user-vote"] = False
            dir = -1

            # Not upvoted or downvoted
            if down_btn.icon_color == ft.colors.WHITE and up_btn.icon_color != ft.colors.ORANGE_300:
                down_btn.icon_color = ft.colors.BLUE_300
                comments_dict[com_id]["score"] = post_likes - 1
                show_score.value = comments_dict[com_id]["score"]
                show_score.color = ft.colors.BLUE_300
            # Was downvoted
            elif down_btn.icon_color == ft.colors.BLUE_300:
                down_btn.icon_color = ft.colors.WHITE
                dir = 0
                comments_dict[com_id]["score"] = post_likes + 1
                show_score.value = comments_dict[com_id]["score"]
                comments_dict[com_id]["user-vote"] = None
                show_score.color = ft.colors.WHITE
            # Was upvoted
            else:
                up_btn.icon_color = ft.colors.WHITE
                down_btn.icon_color = ft.colors.BLUE_300
                comments_dict[com_id]["score"] = post_likes - 2
                show_score.value = comments_dict[com_id]["score"]
                show_score.color = ft.colors.BLUE_300

            com_vote_request = aiohttp.request(method='post', url="https://oauth.reddit.com/api/vote", data={'dir': dir, 'id': com_id}, headers=headers)

            async with com_vote_request as req:
                pass

            await page.update_async()

        # Function to recurse through the comments and design it
        async def recurse_comments(all_info, margin_count):
            nonlocal main_container
            nonlocal comments_dict
            margin_add = margin_count + 34
            for info in all_info:
                if type(info) == str:
                    continue
                if info["kind"] == "Listing":
                    thing_to_go_through = info["data"]["children"]
                    await recurse_comments(thing_to_go_through, margin_add)
                # A comment
                elif info["kind"] == "t1":
                    com_info = info["data"]
                    com_id = com_info["name"]
                    score = com_info["score"]
                    author = com_info["author"]
                    likes = com_info["likes"]
                    com_main = com_info["body"]
                    replies = com_info["replies"]
                    time_created = com_info["created"]

                    # Function to make the vote buttons and callback
                    async def make_com_upvote_btn(comment_id):
                        async def com_upvote_click(e):
                            await update_com_upvote(comment_id)
                            await page.update_async()
                        
                        return ft.IconButton(icon="arrow_upward", icon_color=ft.colors.WHITE, icon_size=17, on_click=com_upvote_click)

                    async def make_com_downvote_btn(comment_id):
                        async def com_downvote_click(e):
                            await update_com_downvote(comment_id)
                            await page.update_async()

                        return ft.IconButton(icon="arrow_downward", icon_color=ft.colors.WHITE, icon_size=17, on_click=com_downvote_click)

                    up_com_btn = await make_com_upvote_btn(com_id)
                    down_com_btn = await make_com_downvote_btn(com_id)

                    score_text = ft.Text(score, size=14, color=ft.colors.WHITE)

                    await toggle_vote_buttons(com_info["likes"], up_com_btn, down_com_btn, score_text)

                    formatted_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime(time_created))

                    # Main content of the comment
                    com_main = ft.Column([
                        ft.Row([ft.Text(author, weight=ft.FontWeight.W_900, size=14), ft.Text(formatted_time, size=10, color=ft.colors.GREY_300, italic=True)], vertical_alignment=ft.CrossAxisAlignment.END),
                        ft.Container(content=ft.Text(com_main, size=16), width=1500-margin_count),
                        ft.Container(content=ft.Row([up_com_btn, ft.Container(content=score_text), down_com_btn], spacing=1), margin=ft.margin.only(left=-12))
                    ])

                    # Formatting the comment
                    com_content = ft.Container(
                        content=com_main,
                        margin=ft.margin.only(left=margin_count, top=5, right=5, bottom=5),
                        alignment=ft.alignment.top_left,
                        border=ft.border.only(left=ft.border.BorderSide(3, ft.colors.WHITE)),
                        padding=ft.padding.only(left=25)
                    )

                    comments_dict[com_id] = {"main": com_main, "author": author, "user-vote": likes, "score": score, "upvote": up_com_btn, "downvote": down_com_btn, "main-view": com_main, "actual-content": com_content, "score-text": score_text}

                    main_container.controls.append(com_content)
                    if replies == '':
                        continue
                    
                    await recurse_comments(replies['data']['children'], margin_add)

        await recurse_comments(info, 47)
        await page.add_async(function_row)
        await page.add_async(main_container)
        await page.update_async()

    await starting_screen()

ft.app(target=main, port=80, view=ft.WEB_BROWSER)