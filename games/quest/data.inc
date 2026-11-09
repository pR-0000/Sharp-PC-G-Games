; Original Quest enemy stats and bilingual text; see NOTICE.md.
enemy_slime:
	.db 16,10,3,10,4,7
	.dw enemy_name_slime

enemy_fantome:
	.db 17,18,5,11,6,10
	.dw enemy_name_fantome

enemy_araignee:
	.db 19,22,6,12,8,13
	.dw enemy_name_araignee

enemy_bandit_ruins:
	.db 20,36,8,13,12,18
	.dw enemy_name_bandit

enemy_bandit_tower:
	.db 20,48,9,15,16,22
	.dw enemy_name_bandit

enemy_squelette:
	.db 18,28,8,12,24,36
	.dw enemy_name_squelette

enemy_bandit_boss:
	.db 20,72,12,16,40,60
	.dw enemy_name_bandit

enemy_demon_ruins:
	.db 21,96,14,18,64,84
	.dw enemy_name_demon

enemy_demon_oasis:
	.db 21,120,16,20,88,108
	.dw enemy_name_demon

enemy_sorcier:
	.db 22,160,20,22,128,160
	.dw enemy_name_sorcier

	IF BUILD_LANG_EN
menu_battle:	; number of options, jump addresses, coordinates (X, Y), zero-terminated string
	.db 3
	.dw battle_attack
	.dw battle_show_objects_menu
	.dw battle_flee
	.db 2,4,"Attack",0
	.db 12,4,"Items",0
	.db 20,4,"Flee",0

menu_objects:
	.db 2
	.dw battle_use_potion
	.dw battle_use_smoke
	.db 4,3,"Potion("
menu_obj_potion_count:
	.db "0","0",")",0
	.db 4,4,"Smoke("
menu_obj_smoke_count:
	.db "0","0",")",0

menu_village:
	.db 3
	.dw village_talk
	.dw village_rest
	.dw village_shop_menu_enter
	.db 3,2,"Talk",0
	.db 3,3,"Inn",0
	.db 3,4,"Shop",0

menu_village_shop:
	.db 4
	.dw shop_buy_potion
	.dw shop_buy_smoke
	.dw shop_buy_blade
	.dw shop_buy_armor
	.db 2,1,"Potion 22",0
	.db 2,2,"Smoke 32",0
	.db 2,3,"Sword +2 144",0
	.db 2,4,"Armor +2 144",0

menu_castle:
	.db 3
	.dw castle_palace
	.dw castle_inn_menu_enter
	.dw castle_shop_menu_enter
	.db 3,1,"Visit king",0
	.db 3,2,"Inn",0
	.db 3,3,"Shop",0

menu_castle_inn:
	.db 2
	.dw castle_inn_yes
	.dw inn_reenter
	.db 3,3,"Yes",0
	.db 3,4,"No",0

menu_castle_shop:
	.db 4
	.dw shop_buy_potion
	.dw shop_buy_smoke
	.dw shop_buy_blade
	.dw shop_buy_armor
	.db 2,1,"Potion 14",0
	.db 2,2,"Smoke 22",0
	.db 2,3,"Sword +1 48",0
	.db 2,4,"Armor +1 48",0

typing_word_ptrs:
	.dw typing_word_blow
	.dw typing_word_rush
	.dw typing_word_slam
	.dw typing_word_stab
	.dw typing_word_strike
	.dw typing_word_charge
	.dw typing_word_thrust
	.dw typing_word_clash
	.dw typing_word_assault
	.dw typing_word_advance
	.dw typing_word_rampage
	.dw typing_word_crush
	.dw typing_word_onslaught
	.dw typing_word_devastate
	.dw typing_word_overpower
	.dw typing_word_annihilate

typing_word_blow:	.db "BLOW",0
typing_word_rush:	.db "RUSH",0
typing_word_slam:	.db "SLAM",0
typing_word_stab:	.db "STAB",0
typing_word_strike:	.db "STRIKE",0
typing_word_charge:	.db "CHARGE",0
typing_word_thrust:	.db "THRUST",0
typing_word_clash:	.db "CLASH",0
typing_word_assault:	.db "ASSAULT",0
typing_word_advance:	.db "ADVANCE",0
typing_word_rampage:	.db "RAMPAGE",0
typing_word_crush:	.db "CRUSH",0
typing_word_onslaught:	.db "ONSLAUGHT",0
typing_word_devastate:	.db "DEVASTATE",0
typing_word_overpower:	.db "OVERPOWER",0
typing_word_annihilate:	.db "ANNIHILATE",0

msg_no_potion:
	.db "No potion",0
msg_no_smoke:
	.db "No smoke",0
msg_full_hp:
	.db "HP full",0
msg_victory:
	.db "Victory!",0
msg_level_up:
	.db "Level up!",0
msg_damage_dealt:
	.db "Dealt: ",0
msg_damage_taken:
	.db "Received: ",0
msg_gold_gain:
	.db "Gold +",0
msg_game_over:
	.db "GAME OVER",0

enemy_name_slime:	.db "SLIME",0
enemy_name_fantome:	.db "GHOST",0
enemy_name_araignee:	.db "SPIDER",0
enemy_name_bandit:	.db "BANDIT",0
enemy_name_squelette:	.db "SKELETON",0
enemy_name_demon:	.db "DEMON",0
enemy_name_sorcier:	.db "SORCERER",0

msg_no_gold:
	.db "Need gold",0
msg_upgrade_owned:
	.db "Already better",0
msg_village:
	.db "Village",0
msg_castle:
	.db "Castle",0
msg_inn:
	.db "Inn",0
msg_inn_offer:
	.db "Rest for "
msg_inn_offer_price:
	.db "20"
	.db " gold?",0
msg_status_title:
	.db "Level ",0
msg_status_hp:
	.db "HP ",0
msg_hud_hp: .db "HP",0
msg_status_pot:
	.db "Potions ",0
msg_status_smoke:
	.db "Smoke ",0
msg_status_sword:
	.db "Sword +",0
msg_status_shield:
	.db "Armor +",0
msg_gold:
	.db "Gold ",0
msg_hero: .db "HERO",0
msg_choose_action: .db "Choose an action",0
msg_fin:
	.db "END",0

intro_text:
	.db "The king needs you.",13
	.db "Explore the graveyard.",13
	.db "Then return to him.",13
	.db "Your quest begins!",0

castle_king_msg_table:
	.dw msg_king_1
	.dw msg_king_2
	.dw msg_king_3
	.dw msg_king_4
	.dw msg_king_4

msg_king_1:
	.db "Explore the forest.",0
msg_king_2:
	.db "Search the ruins.",0
msg_king_3:
	.db "Find the oasis.",0
msg_king_4:
	.db "The black tower awaits.",0

msg_village_0:
	.db "The ruins are east.",13,"Then find the oasis.",0
msg_village_1:
	.db "The tower is southeast.",0

	ELSE
menu_battle:	; number of options, jump addresses, coordinates (X, Y), zero-terminated string
	.db 3
	.dw battle_attack
	.dw battle_show_objects_menu
	.dw battle_flee
	.db 2,4,"Attaquer",0
	.db 12,4,"Objets",0
	.db 20,4,"Fuir",0

menu_objects:
	.db 2
	.dw battle_use_potion
	.dw battle_use_smoke
	.db 4,3,"Potion("
menu_obj_potion_count:
	.db "0","0",")",0
	.db 4,4,"Fum",CHAR_E_ACUTE,"e("
menu_obj_smoke_count:
	.db "0","0",")",0

menu_village:
	.db 3
	.dw village_talk
	.dw village_rest
	.dw village_shop_menu_enter
	.db 3,2,"Parler",0
	.db 3,3,"Auberge",0
	.db 3,4,"Magasin",0

menu_village_shop:
	.db 4
	.dw shop_buy_potion
	.dw shop_buy_smoke
	.dw shop_buy_blade
	.dw shop_buy_armor
	.db 2,1,"Potion 22",0
	.db 2,2,"Fum",CHAR_E_ACUTE,"e 32",0
	.db 2,3,"Epee +2 144",0
	.db 2,4,"Armure +2 144",0

menu_castle:
	.db 3
	.dw castle_palace
	.dw castle_inn_menu_enter
	.dw castle_shop_menu_enter
	.db 3,1,"Voir le roi",0
	.db 3,2,"Auberge",0
	.db 3,3,"Magasin",0

menu_castle_inn:
	.db 2
	.dw castle_inn_yes
	.dw inn_reenter
	.db 3,3,"Oui",0
	.db 3,4,"Non",0

menu_castle_shop:
	.db 4
	.dw shop_buy_potion
	.dw shop_buy_smoke
	.dw shop_buy_blade
	.dw shop_buy_armor
	.db 2,1,"Potion 14",0
	.db 2,2,"Fum",CHAR_E_ACUTE,"e 22",0
	.db 2,3,"Epee +1 48",0
	.db 2,4,"Armure +1 48",0

typing_word_ptrs:
	.dw typing_word_coup
	.dw typing_word_choc
	.dw typing_word_rage
	.dw typing_word_elan
	.dw typing_word_assaut
	.dw typing_word_charge
	.dw typing_word_frappe
	.dw typing_word_ruade
	.dw typing_word_attaque
	.dw typing_word_bagarre
	.dw typing_word_poussee
	.dw typing_word_percee
	.dw typing_word_offensive
	.dw typing_word_bousculade
	.dw typing_word_massacrer
	.dw typing_word_fulgurant

typing_word_coup:	.db "COUP",0
typing_word_choc:	.db "CHOC",0
typing_word_rage:	.db "RAGE",0
typing_word_elan:	.db "ELAN",0
typing_word_assaut:	.db "ASSAUT",0
typing_word_charge:	.db "CHARGE",0
typing_word_frappe:	.db "FRAPPE",0
typing_word_ruade:	.db "RUADE",0
typing_word_attaque:	.db "ATTAQUE",0
typing_word_bagarre:	.db "BAGARRE",0
typing_word_poussee:	.db "POUSSEE",0
typing_word_percee:	.db "PERCEE",0
typing_word_offensive:	.db "OFFENSIVE",0
typing_word_bousculade:	.db "BOUSCULADE",0
typing_word_massacrer:	.db "MASSACRER",0
typing_word_fulgurant:	.db "FULGURANT",0

msg_no_potion:
	.db "Aucune potion",0
msg_no_smoke:
	.db "Aucune fumee",0
msg_full_hp:
	.db "Vie au maximum",0
msg_victory:
	.db "Victoire!",0
msg_level_up:
	.db "Niveau +1",0
msg_damage_dealt:
	.db "Infliges : ",0
msg_damage_taken:
	.db "Recus : ",0
msg_gold_gain:
	.db "Or +",0
msg_game_over:
	.db "FIN DE PARTIE",0

enemy_name_slime:	.db "SLIME",0
enemy_name_fantome:	.db "FANTOME",0
enemy_name_araignee:	.db "ARAIGNEE",0
enemy_name_bandit:	.db "BANDIT",0
enemy_name_squelette:	.db "SQUELETTE",0
enemy_name_demon:	.db "DEMON",0
enemy_name_sorcier:	.db "SORCIER",0

msg_no_gold:
	.db "Or manque",0
msg_upgrade_owned:
	.db "D",CHAR_E_ACUTE,"j",CHAR_A_GRAVE," ",CHAR_E_ACUTE,"quip",CHAR_E_ACUTE,0
msg_village:
	.db "Village",0
msg_castle:
	.db "Ch",CHAR_A_CIRC,"teau",0
msg_inn:
	.db "Auberge",0
msg_inn_offer:
	.db "Repos : "
msg_inn_offer_price:
	.db "20"
	.db " or?",0
msg_status_title:
	.db "Niveau ",0
msg_status_hp:
	.db "PV ",0
msg_hud_hp: .db "PV",0
msg_status_pot:
	.db "Potions ",0
msg_status_smoke:
	.db "Fumees ",0
msg_status_sword:
	.db "Epee +",0
msg_status_shield:
	.db "Armure +",0
msg_gold:
	.db "Or ",0
msg_hero: .db "HEROS",0
msg_choose_action: .db "Choisir une action",0
msg_fin:
	.db "FIN",0

intro_text:
	.db "Le roi te demande :",13
	.db "Explore le cimetiere.",13
	.db "Puis reviens au chateau.",13
	.db "La quete commence !",0

castle_king_msg_table:
	.dw msg_king_1
	.dw msg_king_2
	.dw msg_king_3
	.dw msg_king_4
	.dw msg_king_4

msg_king_1:
	.db "Explore la foret.",0
msg_king_2:
	.db "Fouille les ruines.",0
msg_king_3:
	.db "Rejoins l'oasis.",0
msg_king_4:
	.db "La tour noire t'attend.",0

msg_village_0:
	.db "Ruines vers l'est.",13,"Puis cherche l'oasis.",0
msg_village_1:
	.db "La tour est au sud-est.",0

	ENDIF
